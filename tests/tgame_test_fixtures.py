"""Minimal sparse PE fixtures for the TGame patch-site tests."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

PATCH_TOOLS = Path(__file__).resolve().parents[1] / "tools" / "patches"
if str(PATCH_TOOLS) not in sys.path:
    sys.path.insert(0, str(PATCH_TOOLS))

import tgame_binary  # noqa: E402


IMAGE_BASE = 0x00400000
SECTION_RVA = 0x1000
RAW_POINTER = 0x200


def write_tgame_fixture(path: Path, state: str = "unpatched", *, dynamic_base: bool = False) -> Path:
    path = Path(path)
    patched_stub = tgame_binary.build_trampoline(
        IMAGE_BASE + tgame_binary.TARGET_RVA + len(tgame_binary.EXPECTED_ORIGINAL)
    )
    trampoline_rva = tgame_binary.TARGET_RVA - 0x200
    last_rva = max(
        tgame_binary.TARGET_RVA + tgame_binary.PATCHED_ENTRY_SIZE,
        trampoline_rva + len(patched_stub),
    )
    raw_size = ((last_rva - SECTION_RVA + 0xFFF) // 0x1000) * 0x1000

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        stream.truncate(RAW_POINTER + raw_size)

    dos = bytearray(0x40)
    dos[:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x80)

    optional = bytearray(0xE0)
    struct.pack_into("<H", optional, 0, 0x010B)
    struct.pack_into("<I", optional, 28, IMAGE_BASE)
    struct.pack_into("<I", optional, 60, 0x200)
    dll_characteristics = 0x0040 if dynamic_base else 0
    struct.pack_into("<H", optional, 70, dll_characteristics)

    coff = struct.pack("<HHIIIHH", 0x014C, 1, 0, 0, 0, len(optional), 0x010F)
    section = bytearray(40)
    section[:8] = b".text\0\0\0"
    struct.pack_into("<IIII", section, 8, raw_size, SECTION_RVA, raw_size, RAW_POINTER)
    struct.pack_into("<I", section, 36, 0x60000020)  # code + execute + read

    with path.open("r+b") as stream:
        stream.seek(0)
        stream.write(dos)
        stream.seek(0x80)
        stream.write(b"PE\0\0" + coff + optional + section)

        target_offset = RAW_POINTER + tgame_binary.TARGET_RVA - SECTION_RVA
        if state == "unpatched":
            entry = tgame_binary.EXPECTED_ORIGINAL
        elif state == "patched":
            displacement = trampoline_rva - (tgame_binary.TARGET_RVA + 5)
            entry = b"\xE9" + struct.pack("<i", displacement) + b"\x90\x90\x90"
            trampoline_offset = RAW_POINTER + trampoline_rva - SECTION_RVA
            stream.seek(trampoline_offset)
            stream.write(patched_stub)
        elif state == "bad-trampoline":
            displacement = trampoline_rva - (tgame_binary.TARGET_RVA + 5)
            entry = b"\xE9" + struct.pack("<i", displacement) + b"\x90\x90\x90"
            trampoline_offset = RAW_POINTER + trampoline_rva - SECTION_RVA
            stream.seek(trampoline_offset)
            stream.write(b"\xCC" * len(patched_stub))
        elif state == "unknown":
            entry = b"\xCC" * tgame_binary.PATCHED_ENTRY_SIZE
        else:
            raise ValueError(f"unknown fixture state: {state}")

        stream.seek(target_offset)
        stream.write(entry)
    return path
