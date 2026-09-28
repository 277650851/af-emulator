#!/usr/bin/env python3
"""Recognize the TGame image needed by the launcher's datetime patch.

The whole-file SHA-256 is the primary build check. If it differs, this module
checks the PE32 image and the exact code at the datetime patch site. When the
usual RVA has no file bytes, it accepts only one matching clean signature or a
complete known trampoline in an executable section. Its permanent patch uses
a verified executable code cave or adds a dedicated PE section, and requires
an exact `.bak` backup.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


TARGET_RVA = 0x010B9510
EXPECTED_IMAGE_BASE = 0x00400000
EXPECTED_ORIGINAL = bytes.fromhex("83 EC 24 53 8B 5C 24 2C")
PATCHED_ENTRY_SUFFIX = b"\x90\x90\x90"
PATCHED_ENTRY_SIZE = 8

PE32_MAGIC = 0x010B
IMAGE_FILE_MACHINE_I386 = 0x014C
IMAGE_SCN_MEM_EXECUTE = 0x20000000
IMAGE_SCN_MEM_READ = 0x40000000
IMAGE_SCN_CNT_CODE = 0x00000020
IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040


class TGameBinaryError(ValueError):
    """The file is not a supported, verifiable TGame image."""


class UnbackedRVAError(TGameBinaryError):
    """An RVA exists in a section's virtual image but has no bytes on disk."""


class NoSafeCodeCaveError(TGameBinaryError):
    """No mapped executable fill run is large enough for the trampoline."""


@dataclass(frozen=True)
class Section:
    name: str
    virtual_size: int
    virtual_address: int
    raw_size: int
    raw_pointer: int
    characteristics: int


class PE32Image:
    """Small, bounds-checked PE32 reader for mapping the known code RVA."""

    def __init__(self, path: Path):
        self.path = path
        self.stream = path.open("rb")
        self.file_size = path.stat().st_size
        try:
            self._read_headers()
        except Exception:
            self.stream.close()
            raise

    def close(self) -> None:
        self.stream.close()

    def __enter__(self) -> "PE32Image":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def read_at(self, offset: int, size: int) -> bytes:
        if offset < 0 or size < 0 or offset + size > self.file_size:
            raise TGameBinaryError(
                f"file range 0x{offset:X}+0x{size:X} is outside the image"
            )
        self.stream.seek(offset)
        data = self.stream.read(size)
        if len(data) != size:
            raise TGameBinaryError(
                f"short read at file offset 0x{offset:X}: {len(data)}/{size} bytes"
            )
        return data

    def _read_headers(self) -> None:
        if self.file_size < 0x40 or self.read_at(0, 2) != b"MZ":
            raise TGameBinaryError("missing DOS MZ header")

        pe_offset = struct.unpack("<I", self.read_at(0x3C, 4))[0]
        self.pe_offset = pe_offset
        coff = self.read_at(pe_offset, 24)
        if coff[:4] != b"PE\0\0":
            raise TGameBinaryError("missing PE signature")

        (
            machine,
            section_count,
            _timestamp,
            _symbol_table,
            _symbol_count,
            optional_size,
            _characteristics,
        ) = struct.unpack("<HHIIIHH", coff[4:24])
        if machine != IMAGE_FILE_MACHINE_I386:
            raise TGameBinaryError(f"expected 32-bit x86 PE, found machine 0x{machine:04X}")
        if not 1 <= section_count <= 96:
            raise TGameBinaryError(f"invalid PE section count: {section_count}")
        if optional_size < 72:
            raise TGameBinaryError("PE optional header is too short")

        optional_offset = pe_offset + 24
        self.optional_offset = optional_offset
        optional = self.read_at(optional_offset, optional_size)
        magic = struct.unpack_from("<H", optional, 0)[0]
        if magic != PE32_MAGIC:
            raise TGameBinaryError(f"expected PE32 optional header, found 0x{magic:04X}")

        self.image_base = struct.unpack_from("<I", optional, 28)[0]
        self.section_alignment = struct.unpack_from("<I", optional, 32)[0]
        self.file_alignment = struct.unpack_from("<I", optional, 36)[0]
        self.size_of_image = struct.unpack_from("<I", optional, 56)[0]
        self.size_of_headers = struct.unpack_from("<I", optional, 60)[0]
        self.dll_characteristics = struct.unpack_from("<H", optional, 70)[0]

        section_offset = optional_offset + optional_size
        self.section_table_offset = section_offset
        section_bytes = self.read_at(section_offset, section_count * 40)
        self.sections = []
        for index in range(section_count):
            entry = section_bytes[index * 40 : (index + 1) * 40]
            name = entry[:8].split(b"\0", 1)[0].decode("ascii", errors="replace")
            virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from(
                "<IIII", entry, 8
            )
            characteristics = struct.unpack_from("<I", entry, 36)[0]
            self.sections.append(
                Section(
                    name=name,
                    virtual_size=virtual_size,
                    virtual_address=virtual_address,
                    raw_size=raw_size,
                    raw_pointer=raw_pointer,
                    characteristics=characteristics,
                )
            )

    def section_for_rva(
        self, rva: int, size: int, *, executable: bool = False
    ) -> Section:
        matches = []
        for section in self.sections:
            span = max(section.virtual_size, section.raw_size)
            if section.virtual_address <= rva and rva + size <= section.virtual_address + span:
                matches.append(section)
        if len(matches) != 1:
            raise TGameBinaryError(
                f"RVA 0x{rva:X} is not covered by exactly one PE section"
            )

        section = matches[0]
        delta = rva - section.virtual_address
        if executable and not (section.characteristics & IMAGE_SCN_MEM_EXECUTE):
            raise TGameBinaryError(f"RVA 0x{rva:X} is not in an executable section")
        if delta + size > section.raw_size:
            raise UnbackedRVAError(f"RVA 0x{rva:X} has no backing file bytes")
        return section

    def rva_to_file_offset(
        self, rva: int, size: int, *, executable: bool = False
    ) -> int:
        if rva < self.size_of_headers and rva + size <= self.size_of_headers:
            return rva
        section = self.section_for_rva(rva, size, executable=executable)
        return section.raw_pointer + rva - section.virtual_address

    def read_rva(self, rva: int, size: int, *, executable: bool = False) -> bytes:
        offset = self.rva_to_file_offset(rva, size, executable=executable)
        return self.read_at(offset, size)


def find_original_patch_sites(image: PE32Image) -> list[int]:
    """Find clean patch prologues in file-backed executable sections.

    The exact original bytes are also copied into the verified trampoline.
    Exclude that embedded copy so it cannot be mistaken for a function entry.
    """
    embedded_copy_prefix = bytes.fromhex("C7 44 24 1C FF FF FF FF")
    sites: set[int] = set()
    for section in image.sections:
        if not (section.characteristics & IMAGE_SCN_MEM_EXECUTE):
            continue
        if section.raw_size < len(EXPECTED_ORIGINAL):
            continue
        data = image.read_at(section.raw_pointer, section.raw_size)
        offset = 0
        while True:
            offset = data.find(EXPECTED_ORIGINAL, offset)
            if offset < 0:
                break
            end = offset + len(EXPECTED_ORIGINAL)
            old_static_trampoline = (
                offset >= len(embedded_copy_prefix)
                and data[offset - len(embedded_copy_prefix):offset]
                == embedded_copy_prefix
                and len(data) >= end + 6
                and data[end] == 0x68
                and data[end + 5] == 0xC3
            )
            relative_static_trampoline = (
                offset >= len(embedded_copy_prefix)
                and data[offset - len(embedded_copy_prefix):offset]
                == embedded_copy_prefix
                and len(data) >= end + 5
                and data[end] == 0xE9
            )
            if not (old_static_trampoline or relative_static_trampoline):
                sites.add(section.virtual_address + offset)
            offset += 1
    return sorted(sites)


def find_static_patch_sites(image: PE32Image) -> list[int]:
    """Find entries that reach an exact supported on-disk trampoline."""
    sites: set[int] = set()
    for section in image.sections:
        if not (section.characteristics & IMAGE_SCN_MEM_EXECUTE):
            continue
        if section.raw_size < PATCHED_ENTRY_SIZE:
            continue
        data = image.read_at(section.raw_pointer, section.raw_size)
        offset = data.find(b"\xE9")
        while offset >= 0 and offset + PATCHED_ENTRY_SIZE <= len(data):
            entry = data[offset : offset + PATCHED_ENTRY_SIZE]
            if is_patched_entry(entry):
                site_rva = section.virtual_address + offset
                displacement = struct.unpack("<i", entry[1:5])[0]
                trampoline_rva = site_rva + 5 + displacement
                kind = _static_trampoline_kind(image, site_rva, trampoline_rva)
                if kind == "position-independent":
                    sites.add(site_rva)
                    offset = data.find(b"\xE9", offset + 1)
                    continue

                # Earlier development builds used an absolute `push VA; ret`
                # tail. It is valid only when Windows will not relocate the
                # image, so retain recognition for fixed-base files only.
                if (
                    kind == "absolute"
                    and not (image.dll_characteristics & IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE)
                ):
                    sites.add(site_rva)
            offset = data.find(b"\xE9", offset + 1)
    return sorted(sites)


def _build_datetime_prefix() -> bytearray:
    code = bytearray.fromhex("81 7C 24 04 6C 07 00 00 7D 38")
    fixes = (
        (0x04, 2026),
        (0x08, 9),
        (0x0C, 19),
        (0x10, 12),
        (0x14, 0),
        (0x18, 0),
        (0x1C, 0xFFFFFFFF),
    )
    for displacement, value in fixes:
        code += b"\xC7\x44\x24" + bytes((displacement,))
        code += struct.pack("<I", value & 0xFFFFFFFF)
    return code


def build_trampoline(return_va: int) -> bytes:
    """Build the runtime trampoline, which returns to an absolute VA."""
    code = _build_datetime_prefix()
    code += EXPECTED_ORIGINAL
    code += b"\x68" + struct.pack("<I", return_va & 0xFFFFFFFF) + b"\xC3"
    return bytes(code)


def build_static_trampoline(site_rva: int, trampoline_rva: int) -> bytes:
    """Build a position-independent trampoline for a permanent file patch."""
    code = _build_datetime_prefix()
    code += EXPECTED_ORIGINAL
    continuation_rva = site_rva + len(EXPECTED_ORIGINAL)
    displacement = continuation_rva - (trampoline_rva + len(code) + 5)
    if not -(2**31) <= displacement < 2**31:
        raise TGameBinaryError("static trampoline is outside the x86 rel32 range")
    code += b"\xE9" + struct.pack("<i", displacement)
    return bytes(code)


def _static_trampoline_kind(
    image: PE32Image, site_rva: int, trampoline_rva: int
) -> str | None:
    """Return the recognized on-disk trampoline format at an executable RVA."""
    position_independent = build_static_trampoline(site_rva, trampoline_rva)
    try:
        if image.read_rva(
            trampoline_rva, len(position_independent), executable=True
        ) == position_independent:
            return "position-independent"
    except TGameBinaryError:
        pass

    absolute = build_trampoline(
        image.image_base + site_rva + len(EXPECTED_ORIGINAL)
    )
    try:
        if image.read_rva(trampoline_rva, len(absolute), executable=True) == absolute:
            return "absolute"
    except TGameBinaryError:
        pass
    return None


def is_patched_entry(entry: bytes) -> bool:
    return (
        len(entry) == PATCHED_ENTRY_SIZE
        and entry[0] == 0xE9
        and entry[5:] == PATCHED_ENTRY_SUFFIX
    )


def matches_runtime_patch(
    entry: bytes,
    site_va: int,
    continuation_va: int,
    read_memory: Callable[[int, int], bytes],
) -> bool:
    """Check a live TGame entry and its trampoline before skipping a re-patch."""
    if not is_patched_entry(entry):
        return False
    displacement = struct.unpack("<i", entry[1:5])[0]
    trampoline_va = site_va + 5 + displacement
    static_stub = build_static_trampoline(site_va, trampoline_va)
    try:
        actual_static_stub = read_memory(trampoline_va, len(static_stub))
    except Exception:
        actual_static_stub = b""
    if actual_static_stub == static_stub:
        return True
    runtime_stub = build_trampoline(continuation_va)
    try:
        actual_runtime_stub = read_memory(trampoline_va, len(runtime_stub))
    except Exception:
        return False
    return actual_runtime_stub == runtime_stub


def _find_code_cave(
    image: PE32Image, size: int, site_rva: int
) -> tuple[int, int]:
    """Find the closest aligned run of mapped executable-section fill bytes."""
    candidates: list[tuple[int, int, int, int]] = []
    for section in image.sections:
        if not (section.characteristics & IMAGE_SCN_MEM_EXECUTE):
            continue
        mapped_raw_size = min(
            section.raw_size,
            section.virtual_size if section.virtual_size else section.raw_size,
        )
        if mapped_raw_size < size:
            continue

        data = image.read_at(section.raw_pointer, mapped_raw_size)
        run_start: int | None = None

        def record_run(start: int, end: int) -> None:
            start_rva = section.virtual_address + start
            end_rva = section.virtual_address + end
            cave_rva = (start_rva + 15) & ~15
            entry_end = site_rva + PATCHED_ENTRY_SIZE
            displacement = cave_rva - (site_rva + 5)
            if cave_rva + size > end_rva:
                return
            if cave_rva < entry_end and cave_rva + size > site_rva:
                return
            if not -(2**31) <= displacement < 2**31:
                return
            available = end_rva - cave_rva
            candidates.append(
                (
                    abs(cave_rva - site_rva),
                    -available,
                    cave_rva,
                    section.raw_pointer + cave_rva - section.virtual_address,
                )
            )

        for offset, value in enumerate(data):
            if value in (0x00, 0xCC):
                if run_start is None:
                    run_start = offset
            elif run_start is not None:
                record_run(run_start, offset)
                run_start = None
        if run_start is not None:
            record_run(run_start, len(data))

    if not candidates:
        raise NoSafeCodeCaveError(
            f"no {size}-byte executable code cave made of 0x00/0xCC fill "
            "was found in any mapped executable section"
        )
    candidates.sort()
    if len(candidates) > 1 and candidates[0][:2] == candidates[1][:2]:
        raise TGameBinaryError(
            "multiple equally suitable executable code caves were found; "
            "refusing an ambiguous permanent patch"
        )
    return candidates[0][2], candidates[0][3]


def _align_up(value: int, alignment: int) -> int:
    if alignment <= 0 or alignment & (alignment - 1):
        raise TGameBinaryError(f"invalid PE alignment value: 0x{alignment:X}")
    return (value + alignment - 1) & ~(alignment - 1)


def _append_trampoline_section(
    original_data: bytes, image: PE32Image, site_rva: int, trampoline_size: int
) -> tuple[bytearray, int, bytes]:
    """Append a mapped executable section for the trampoline when caves are absent."""
    if len(image.sections) >= 96:
        raise TGameBinaryError("cannot add the datetime section: PE section limit reached")
    if image.file_alignment <= 0 or image.section_alignment <= 0:
        raise TGameBinaryError(
            "cannot add the datetime section: PE file/section alignments are invalid"
        )
    if (
        image.file_alignment & (image.file_alignment - 1)
        or image.section_alignment & (image.section_alignment - 1)
        or image.file_alignment > image.section_alignment
        or (
            image.section_alignment < 0x1000
            and image.file_alignment != image.section_alignment
        )
        or (
            image.section_alignment >= 0x1000
            and not 0x200 <= image.file_alignment <= 0x10000
        )
    ):
        raise TGameBinaryError(
            "cannot add the datetime section: PE file/section alignments are invalid"
        )
    if any(section.name == ".afdt" for section in image.sections):
        raise TGameBinaryError(
            "cannot add the datetime section: a section named '.afdt' already exists"
        )

    section_header_offset = image.section_table_offset + len(image.sections) * 40
    section_header_end = section_header_offset + 40
    raw_section_starts = [
        section.raw_pointer for section in image.sections if section.raw_pointer
    ]
    first_raw_offset = min(raw_section_starts, default=image.file_size)
    if (
        section_header_end > image.size_of_headers
        or section_header_end > first_raw_offset
        or section_header_end > image.file_size
    ):
        raise TGameBinaryError(
            "cannot add the datetime section: no free 40-byte section-header slot"
        )
    if any(original_data[section_header_offset:section_header_end]):
        raise TGameBinaryError(
            "cannot add the datetime section: section-header slot is not unused"
        )

    virtual_end = max(
        section.virtual_address + max(section.virtual_size, section.raw_size)
        for section in image.sections
    )
    new_rva = _align_up(virtual_end, image.section_alignment)
    raw_size = _align_up(trampoline_size, image.file_alignment)
    raw_pointer = _align_up(len(original_data), image.file_alignment)
    entry_displacement = new_rva - (site_rva + 5)
    if not -(2**31) <= entry_displacement < 2**31:
        raise TGameBinaryError(
            "cannot add the datetime section: trampoline is outside the x86 entry-jump range"
        )
    if max(new_rva + trampoline_size, raw_pointer + raw_size) > 0xFFFFFFFF:
        raise TGameBinaryError(
            "cannot add the datetime section: PE32 address range exceeded"
        )

    trampoline = build_static_trampoline(site_rva, new_rva)
    if len(trampoline) != trampoline_size:
        raise TGameBinaryError("datetime trampoline size changed during section creation")

    section_characteristics = (
        IMAGE_SCN_CNT_CODE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ
    )
    section_header = struct.pack(
        "<8sIIIIIIHHI",
        b".afdt\0\0\0",
        trampoline_size,
        new_rva,
        raw_size,
        raw_pointer,
        0,
        0,
        0,
        0,
        section_characteristics,
    )

    patched_data = bytearray(original_data)
    patched_data[section_header_offset:section_header_end] = section_header
    if raw_pointer > len(patched_data):
        patched_data.extend(b"\0" * (raw_pointer - len(patched_data)))
    patched_data.extend(trampoline)
    patched_data.extend(b"\xCC" * (raw_size - len(trampoline)))

    struct.pack_into("<H", patched_data, image.pe_offset + 6, len(image.sections) + 1)
    optional = image.optional_offset
    old_size_of_code = struct.unpack_from("<I", patched_data, optional + 4)[0]
    if old_size_of_code + raw_size > 0xFFFFFFFF:
        raise TGameBinaryError(
            "cannot add the datetime section: PE32 code size overflow"
        )
    struct.pack_into("<I", patched_data, optional + 4, old_size_of_code + raw_size)
    new_size_of_image = max(
        image.size_of_image,
        _align_up(
            new_rva + max(trampoline_size, raw_size), image.section_alignment
        ),
    )
    if new_size_of_image > 0xFFFFFFFF:
        raise TGameBinaryError(
            "cannot add the datetime section: PE32 image size overflow"
        )
    struct.pack_into("<I", patched_data, optional + 56, new_size_of_image)
    struct.pack_into("<I", patched_data, optional + 64, 0)  # Clear stale PE checksum.
    return patched_data, new_rva, trampoline


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _write_sibling_temp(target: Path, data: bytes, metadata_source: Path) -> Path:
    fd, name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        shutil.copystat(metadata_source, temporary)
        return temporary
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _atomic_replace(target: Path, replacement: Path) -> None:
    if os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        replace_file = kernel32.ReplaceFileW
        replace_file.argtypes = (
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_void_p,
        )
        replace_file.restype = ctypes.c_int
        if not replace_file(str(target), str(replacement), None, 0, None, None):
            raise ctypes.WinError(ctypes.get_last_error())
        return
    os.replace(replacement, target)


def apply_static_datetime_patch(
    path: str | Path, backup_path: str | Path | None = None
) -> dict[str, str]:
    """Permanently patch a verified TGame file, preserving a byte-exact backup.

    Only a unique, file-backed clean patch site is accepted. The trampoline
    uses a nearby aligned executable-section 0x00/0xCC fill run when available;
    otherwise a dedicated executable PE section is added only when the headers
    have an unused slot. The replacement is validated and atomically installed
    after the original backup has been verified.
    """
    target = Path(path)
    backup = Path(backup_path) if backup_path else Path(str(target) + ".bak")
    if target.resolve() == backup.resolve():
        raise TGameBinaryError("backup path must not refer to TGame.exe itself")

    classification = classify_tgame_binary(target)
    if classification["status"] == "unsupported":
        raise TGameBinaryError(
            "TGame file was not changed because its patch site is not verified: "
            + classification["message"]
        )
    if classification["status"] == "already-patched":
        return {
            "status": "already-patched",
            "path": str(target),
            "target_rva": classification.get("target_rva", ""),
            "message": "The exact datetime patch and trampoline are already present.",
        }

    try:
        site_rva = int(classification["target_rva"], 0)
    except (KeyError, TypeError, ValueError) as exc:
        raise TGameBinaryError("binary checker returned an invalid target RVA") from exc

    original_digest = _file_sha256(target)
    original_data = target.read_bytes()
    if _sha256(original_data) != original_digest:
        raise TGameBinaryError("TGame.exe changed while it was being inspected")

    trampoline_storage = "existing-code-cave"
    with PE32Image(target) as image:
        site_offset = image.rva_to_file_offset(
            site_rva, len(EXPECTED_ORIGINAL), executable=True
        )
        if original_data[site_offset : site_offset + len(EXPECTED_ORIGINAL)] != EXPECTED_ORIGINAL:
            raise TGameBinaryError(
                "TGame patch-site bytes changed after signature validation; file was not modified"
            )
        image.section_for_rva(site_rva, len(EXPECTED_ORIGINAL), executable=True)
        stub_length = (
            len(_build_datetime_prefix()) + len(EXPECTED_ORIGINAL) + 5
        )
        try:
            trampoline_rva, trampoline_offset = _find_code_cave(
                image, stub_length, site_rva
            )
        except NoSafeCodeCaveError:
            patched_data, trampoline_rva, trampoline = _append_trampoline_section(
                original_data, image, site_rva, stub_length
            )
            trampoline_storage = "new-.afdt-section"
        else:
            cave_before = original_data[
                trampoline_offset : trampoline_offset + stub_length
            ]
            if len(cave_before) != stub_length:
                raise TGameBinaryError("selected code cave extends beyond the TGame file")
            if any(value not in (0x00, 0xCC) for value in cave_before):
                raise TGameBinaryError(
                    "selected code cave changed or contains non-fill bytes"
                )
            trampoline = build_static_trampoline(site_rva, trampoline_rva)
            patched_data = bytearray(original_data)
            patched_data[
                trampoline_offset : trampoline_offset + len(trampoline)
            ] = trampoline

        entry_displacement = trampoline_rva - (site_rva + 5)
        if not -(2**31) <= entry_displacement < 2**31:
            raise TGameBinaryError(
                "datetime trampoline is outside the x86 entry-jump range"
            )
        entry_patch = (
            b"\xE9"
            + struct.pack("<i", entry_displacement)
            + PATCHED_ENTRY_SUFFIX
        )
    patched_data[site_offset : site_offset + len(entry_patch)] = entry_patch

    temporary = _write_sibling_temp(target, bytes(patched_data), target)
    try:
        verified = classify_tgame_binary(temporary)
        if (
            verified["status"] != "already-patched"
            or verified.get("target_rva") != f"0x{site_rva:08X}"
        ):
            raise TGameBinaryError(
                "temporary patched TGame failed read-back validation: "
                + verified["message"]
            )

        if backup.exists():
            if _file_sha256(backup) != original_digest:
                raise TGameBinaryError(
                    f"backup already exists but does not match the original TGame.exe: {backup}"
                )
        else:
            shutil.copy2(target, backup)
            if _file_sha256(backup) != original_digest:
                backup.unlink(missing_ok=True)
                raise TGameBinaryError("byte-exact TGame.exe backup verification failed")

        if _file_sha256(target) != original_digest:
            raise TGameBinaryError("TGame.exe changed before replacement; no patch was installed")
        _atomic_replace(target, temporary)

        installed = classify_tgame_binary(target)
        if (
            installed["status"] != "already-patched"
            or installed.get("target_rva") != f"0x{site_rva:08X}"
        ):
            rollback = _write_sibling_temp(target, backup.read_bytes(), backup)
            try:
                _atomic_replace(target, rollback)
            finally:
                rollback.unlink(missing_ok=True)
            raise TGameBinaryError(
                "installed TGame patch failed read-back validation; the original was restored from backup"
            )

        return {
            "status": "patched",
            "path": str(target),
            "backup_path": str(backup),
            "original_sha256": original_digest,
            "patched_sha256": _file_sha256(target),
            "target_rva": f"0x{site_rva:08X}",
            "trampoline_rva": f"0x{trampoline_rva:08X}",
            "trampoline_storage": trampoline_storage,
            "message": "Permanent TGame datetime patch applied and verified.",
        }
    finally:
        temporary.unlink(missing_ok=True)


def classify_tgame_binary(path: str | Path) -> dict[str, str]:
    """Return a supported patch-site state or a detailed unsupported result."""
    target = Path(path)
    try:
        with PE32Image(target) as image:
            if image.image_base != EXPECTED_IMAGE_BASE:
                raise TGameBinaryError(
                    f"expected image base 0x{EXPECTED_IMAGE_BASE:08X}, "
                    f"found 0x{image.image_base:08X}"
                )

            entry = image.read_rva(TARGET_RVA, PATCHED_ENTRY_SIZE, executable=True)
            if entry == EXPECTED_ORIGINAL:
                return {
                    "status": "unpatched-compatible",
                    "target_rva": f"0x{TARGET_RVA:08X}",
                    "message": (
                        f"PE32/i386 patch site RVA 0x{TARGET_RVA:08X} matches the "
                        "exact original instructions required by the runtime patcher."
                    ),
                }

            if is_patched_entry(entry):
                displacement = struct.unpack("<i", entry[1:5])[0]
                trampoline_rva = TARGET_RVA + 5 + displacement
                kind = _static_trampoline_kind(image, TARGET_RVA, trampoline_rva)
                if kind is None:
                    raise TGameBinaryError(
                        "the patch-site jump exists, but its target does not match "
                        "the verified datetime trampoline"
                    )
                if (
                    kind == "absolute"
                    and image.dll_characteristics & IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE
                ):
                    raise TGameBinaryError(
                        "the static datetime patch is not accepted in a relocatable "
                        "image because its trampoline contains an absolute return address"
                    )
                return {
                    "status": "already-patched",
                    "target_rva": f"0x{TARGET_RVA:08X}",
                    "message": (
                        f"PE32/i386 patch site RVA 0x{TARGET_RVA:08X} and its complete "
                        "datetime trampoline match the verified patch. "
                        f"Trampoline type: {kind}."
                    ),
                }

            raise TGameBinaryError(
                f"unexpected bytes at RVA 0x{TARGET_RVA:08X}: {entry.hex(' ').upper()}"
            )
    except UnbackedRVAError as exc:
        try:
            with PE32Image(target) as image:
                original_sites = find_original_patch_sites(image)
                patched_sites = find_static_patch_sites(image)
        except (OSError, TGameBinaryError, struct.error) as scan_exc:
            return {"status": "unsupported", "message": str(scan_exc)}

        if len(original_sites) == 1 and not patched_sites:
            site = original_sites[0]
            return {
                "status": "unpatched-compatible",
                "target_rva": f"0x{site:08X}",
                "message": (
                    f"{exc}; found the exact clean patch prologue at the unique "
                    f"executable-section signature RVA 0x{site:08X}. The runtime "
                    "patcher will recheck these bytes in the loaded TGame process."
                ),
            }
        if len(patched_sites) == 1 and not original_sites:
            site = patched_sites[0]
            return {
                "status": "already-patched",
                "target_rva": f"0x{site:08X}",
                "message": (
                    f"{exc}; found the exact datetime entry jump and trampoline at "
                    f"the unique executable-section signature RVA 0x{site:08X}."
                ),
            }
        if not original_sites and not patched_sites:
            return {
                "status": "unsupported",
                "message": (
                    f"{exc}; no matching executable-section signature was found"
                ),
            }
        return {
            "status": "unsupported",
            "message": (
                f"{exc}; found {len(original_sites)} clean and "
                f"{len(patched_sites)} patched executable-section signatures, "
                "so the patch target is ambiguous"
            ),
        }
    except (OSError, TGameBinaryError, struct.error) as exc:
        return {"status": "unsupported", "message": str(exc)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print a JSON result")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="apply the verified permanent patch and save TGame.exe.bak",
    )
    parser.add_argument("path", help="TGame.exe to inspect or patch")
    args = parser.parse_args(argv)

    if args.apply:
        try:
            result = apply_static_datetime_patch(args.path)
            exit_code = 0
        except (OSError, TGameBinaryError, struct.error) as exc:
            result = {"status": "unsupported", "message": str(exc)}
            exit_code = 1
    else:
        result = classify_tgame_binary(args.path)
        exit_code = 0 if result["status"] != "unsupported" else 1
    if args.json:
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(f"[{result['status']}] {result['message']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
