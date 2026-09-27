#!/usr/bin/env python3
"""Recognize the TGame image needed by the launcher's datetime patch.

The whole-file SHA-256 is the primary build check. If it differs, this module
checks the PE32 image and the exact code at the datetime patch site. When the
usual RVA has no file bytes, it accepts only one matching clean signature or a
complete known trampoline in an executable section.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
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
IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040


class TGameBinaryError(ValueError):
    """The file is not a supported, verifiable TGame image."""


class UnbackedRVAError(TGameBinaryError):
    """An RVA exists in a section's virtual image but has no bytes on disk."""


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
        optional = self.read_at(optional_offset, optional_size)
        magic = struct.unpack_from("<H", optional, 0)[0]
        if magic != PE32_MAGIC:
            raise TGameBinaryError(f"expected PE32 optional header, found 0x{magic:04X}")

        self.image_base = struct.unpack_from("<I", optional, 28)[0]
        self.size_of_headers = struct.unpack_from("<I", optional, 60)[0]
        self.dll_characteristics = struct.unpack_from("<H", optional, 70)[0]

        section_offset = optional_offset + optional_size
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

    def read_rva(self, rva: int, size: int, *, executable: bool = False) -> bytes:
        if rva < self.size_of_headers and rva + size <= self.size_of_headers:
            return self.read_at(rva, size)

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
        return self.read_at(section.raw_pointer + delta, size)


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
            embedded_copy = (
                offset >= len(embedded_copy_prefix)
                and data[offset - len(embedded_copy_prefix):offset]
                == embedded_copy_prefix
                and len(data) >= end + 6
                and data[end] == 0x68
                and data[end + 5] == 0xC3
            )
            if not embedded_copy:
                sites.add(section.virtual_address + offset)
            offset += 1
    return sorted(sites)


def find_static_patch_sites(image: PE32Image) -> list[int]:
    """Find entries whose jump reaches the exact supported file trampoline."""
    if image.dll_characteristics & IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE:
        return []

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
                expected_stub = build_trampoline(
                    image.image_base + site_rva + len(EXPECTED_ORIGINAL)
                )
                try:
                    actual_stub = image.read_rva(
                        trampoline_rva, len(expected_stub), executable=True
                    )
                except TGameBinaryError:
                    actual_stub = b""
                if actual_stub == expected_stub:
                    sites.add(site_rva)
            offset = data.find(b"\xE9", offset + 1)
    return sorted(sites)


def build_trampoline(return_va: int) -> bytes:
    """Build the exact instruction sequence used by the runtime datetime fix."""
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
    code += EXPECTED_ORIGINAL
    code += b"\x68" + struct.pack("<I", return_va & 0xFFFFFFFF) + b"\xC3"
    return bytes(code)


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
    try:
        actual_stub = read_memory(trampoline_va, len(build_trampoline(continuation_va)))
    except Exception:
        return False
    return actual_stub == build_trampoline(continuation_va)


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
                expected_stub = build_trampoline(
                    image.image_base + TARGET_RVA + len(EXPECTED_ORIGINAL)
                )
                stub = image.read_rva(
                    trampoline_rva, len(expected_stub), executable=True
                )
                if stub != expected_stub:
                    raise TGameBinaryError(
                        "the patch-site jump exists, but its target does not match "
                        "the verified datetime trampoline"
                    )
                if image.dll_characteristics & IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE:
                    raise TGameBinaryError(
                        "the static datetime patch is not accepted in a relocatable "
                        "image because its trampoline contains an absolute return address"
                    )
                return {
                    "status": "already-patched",
                    "target_rva": f"0x{TARGET_RVA:08X}",
                    "message": (
                        f"PE32/i386 patch site RVA 0x{TARGET_RVA:08X} and its complete "
                        "datetime trampoline match the verified patch."
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
    parser.add_argument("path", help="TGame.exe to inspect")
    args = parser.parse_args(argv)

    result = classify_tgame_binary(args.path)
    if args.json:
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(f"[{result['status']}] {result['message']}")
    return 0 if result["status"] != "unsupported" else 1


if __name__ == "__main__":
    raise SystemExit(main())
