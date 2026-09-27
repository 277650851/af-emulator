#!/usr/bin/env python3
"""
Assault Fire / TGame datetime runtime patcher.

Purpose
-------
Automates the x32dbg patch we proved manually at TGame.exe+0x10B9510
(VA 0x014B9510 when the image base is 0x00400000).

When that function is entered with year < 1900, the injected trampoline
replaces the seven date/time arguments with:

    year   = 2026
    month  = 9
    day    = 19
    hour   = 12
    minute = 0
    second = 0
    isdst  = -1

Then it executes the original overwritten prologue and returns to the
original TGame code at +8.

This is a *runtime-only* patch. It does not modify TGame.exe on disk.

Usage
-----
    python patch_tgame_datetime.py

You can start this script first and then launch TGame.exe.  It waits for
TGame.exe, patches it once, prints PATCHED, and exits.

Run the terminal as Administrator if OpenProcess/WriteProcessMemory is denied.
"""

import ctypes
import os
import struct
import sys
import time
from ctypes import wintypes

try:
    import launch_preflight_gate as launch_gate
    import tgame_binary
except Exception as exc:
    raise SystemExit(
        "Could not import required helpers from tools/patches. "
        "Keep the repository files together.\n"
        f"Import error: {exc}"
    )

if os.name != "nt":
    raise SystemExit("This patcher must be run on Windows.")

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ---------------------------------------------------------------------------
# Target build / patch constants
# ---------------------------------------------------------------------------

PROCESS_NAME = "TGame.exe"

TARGET_RVA = tgame_binary.TARGET_RVA
EXPECTED_ORIGINAL = tgame_binary.EXPECTED_ORIGINAL

# Process access rights.
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000

PAGE_EXECUTE_READWRITE = 0x40

TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
MAX_PATH = 260


# ---------------------------------------------------------------------------
# Toolhelp structures
# ---------------------------------------------------------------------------

ULONG_PTR = ctypes.c_size_t


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ULONG_PTR),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * MAX_PATH),
    ]


class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_ubyte)),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", wintypes.WCHAR * 256),
        ("szExePath", wintypes.WCHAR * MAX_PATH),
    ]


# ---------------------------------------------------------------------------
# WinAPI prototypes
# ---------------------------------------------------------------------------

kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE

kernel32.Process32FirstW.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESSENTRY32W),
]
kernel32.Process32FirstW.restype = wintypes.BOOL

kernel32.Process32NextW.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESSENTRY32W),
]
kernel32.Process32NextW.restype = wintypes.BOOL

kernel32.Module32FirstW.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(MODULEENTRY32W),
]
kernel32.Module32FirstW.restype = wintypes.BOOL

kernel32.Module32NextW.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(MODULEENTRY32W),
]
kernel32.Module32NextW.restype = wintypes.BOOL

kernel32.OpenProcess.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.DWORD,
]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.ReadProcessMemory.restype = wintypes.BOOL

kernel32.WriteProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.LPCVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.WriteProcessMemory.restype = wintypes.BOOL

kernel32.VirtualAllocEx.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    ctypes.c_size_t,
    wintypes.DWORD,
    wintypes.DWORD,
]
kernel32.VirtualAllocEx.restype = wintypes.LPVOID

kernel32.FlushInstructionCache.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    ctypes.c_size_t,
]
kernel32.FlushInstructionCache.restype = wintypes.BOOL

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


def winerr(prefix):
    err = ctypes.get_last_error()
    return RuntimeError(f"{prefix} failed: WinError {err}: {ctypes.FormatError(err).strip()}")


def find_processes(exe_name):
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID_HANDLE_VALUE:
        raise winerr("CreateToolhelp32Snapshot(PROCESS)")

    out = []
    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(pe)

        ok = kernel32.Process32FirstW(snap, ctypes.byref(pe))
        while ok:
            if pe.szExeFile.lower() == exe_name.lower():
                out.append(int(pe.th32ProcessID))
            ok = kernel32.Process32NextW(snap, ctypes.byref(pe))
    finally:
        kernel32.CloseHandle(snap)

    return out


def find_module_info(pid, module_name):
    flags = TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32
    snap = kernel32.CreateToolhelp32Snapshot(flags, pid)
    if snap == INVALID_HANDLE_VALUE:
        return None, None

    try:
        me = MODULEENTRY32W()
        me.dwSize = ctypes.sizeof(me)

        ok = kernel32.Module32FirstW(snap, ctypes.byref(me))
        while ok:
            if me.szModule.lower() == module_name.lower():
                return (
                    ctypes.cast(me.modBaseAddr, ctypes.c_void_p).value,
                    str(me.szExePath),
                )

            ok = kernel32.Module32NextW(snap, ctypes.byref(me))
    finally:
        kernel32.CloseHandle(snap)

    return None, None


def read_memory(process, address, size):
    buf = (ctypes.c_ubyte * size)()
    got = ctypes.c_size_t(0)

    if not kernel32.ReadProcessMemory(
        process,
        ctypes.c_void_p(address),
        buf,
        size,
        ctypes.byref(got),
    ):
        raise winerr(f"ReadProcessMemory(0x{address:08X})")

    if got.value != size:
        raise RuntimeError(
            f"short ReadProcessMemory at 0x{address:08X}: "
            f"{got.value}/{size} bytes"
        )

    return bytes(buf)


def write_memory(process, address, data):
    raw = bytes(data)
    buf = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    wrote = ctypes.c_size_t(0)

    if not kernel32.WriteProcessMemory(
        process,
        ctypes.c_void_p(address),
        buf,
        len(raw),
        ctypes.byref(wrote),
    ):
        raise winerr(f"WriteProcessMemory(0x{address:08X})")

    if wrote.value != len(raw):
        raise RuntimeError(
            f"short WriteProcessMemory at 0x{address:08X}: "
            f"{wrote.value}/{len(raw)} bytes"
        )


def patch_process(pid, base):
    access = (
        PROCESS_QUERY_INFORMATION
        | PROCESS_VM_OPERATION
        | PROCESS_VM_READ
        | PROCESS_VM_WRITE
    )

    process = kernel32.OpenProcess(access, False, pid)
    if not process:
        raise winerr("OpenProcess")

    try:
        target = base + TARGET_RVA
        continuation = target + len(EXPECTED_ORIGINAL)

        original = read_memory(process, target, len(EXPECTED_ORIGINAL))

        if original != EXPECTED_ORIGINAL:
            if tgame_binary.matches_runtime_patch(
                original,
                target,
                continuation,
                lambda address, size: read_memory(process, address, size),
            ):
                print()
                print("PATCHED (already active)")
                print(f"  PID          : {pid}")
                print(f"  TGame base   : 0x{base:08X}")
                print(f"  target       : 0x{target:08X}")
                print()
                print("The verified datetime trampoline is already active.")
                return

            raise RuntimeError(
                "TGame build/signature mismatch.\n"
                f"Expected at 0x{target:08X}: {EXPECTED_ORIGINAL.hex(' ')}\n"
                f"Found:                    {original.hex(' ')}\n"
                "Nothing was patched."
            )

        stub = tgame_binary.build_trampoline(continuation)

        remote = kernel32.VirtualAllocEx(
            process,
            None,
            max(0x1000, len(stub)),
            MEM_COMMIT | MEM_RESERVE,
            PAGE_EXECUTE_READWRITE,
        )
        if not remote:
            raise winerr("VirtualAllocEx")

        remote_addr = ctypes.cast(remote, ctypes.c_void_p).value

        write_memory(process, remote_addr, stub)

        # JMP rel32 from TGame function entry to our trampoline.
        rel32 = (remote_addr - (target + 5)) & 0xFFFFFFFF
        entry_patch = b"\xE9" + struct.pack("<I", rel32) + b"\x90\x90\x90"

        write_memory(process, target, entry_patch)

        kernel32.FlushInstructionCache(
            process,
            ctypes.c_void_p(target),
            len(entry_patch),
        )
        kernel32.FlushInstructionCache(
            process,
            ctypes.c_void_p(remote_addr),
            len(stub),
        )

        verify = read_memory(process, target, len(entry_patch))
        if verify != entry_patch:
            raise RuntimeError(
                "patch verification failed: "
                f"read back {verify.hex(' ')}"
            )

        print()
        print("PATCHED")
        print(f"  PID          : {pid}")
        print(f"  TGame base   : 0x{base:08X}")
        print(f"  target       : 0x{target:08X}")
        print(f"  trampoline   : 0x{remote_addr:08X}")
        print(f"  continuation : 0x{continuation:08X}")
        print()
        print("Datetime fix is active for this TGame process.")
        print("You can leave x32dbg's 014B9510 breakpoint disabled.")

    finally:
        kernel32.CloseHandle(process)


def main():
    timeout = 300.0
    start = time.time()

    gate_status = launch_gate.require_launch_ready()
    print("[LAUNCH-GATE] PASS - server preflight is UNLOCKED.")
    print(f"[LAUNCH-GATE] client root: {gate_status.get('client_root')}")
    print()

    existing_pids = set(find_processes(PROCESS_NAME))
    if existing_pids:
        print(
            "Existing TGame PID(s) will be ignored: "
            + ", ".join(str(x) for x in sorted(existing_pids))
        )

    print(f"Waiting for a new {PROCESS_NAME} from the preflight-approved client ...")
    print("You can launch the game now.")
    print()

    announced = set()

    while True:
        if time.time() - start > timeout:
            raise SystemExit(
                f"Timed out after {int(timeout)} seconds waiting for {PROCESS_NAME}."
            )

        candidates = [
            pid for pid in find_processes(PROCESS_NAME)
            if pid not in existing_pids
        ]
        matched = None
        for pid in candidates:
            base, image_path = find_module_info(pid, PROCESS_NAME)
            if not base or not image_path:
                continue
            if pid not in announced:
                print(
                    f"Found {PROCESS_NAME} PID={pid}; image={image_path}"
                )
                announced.add(pid)
            try:
                gate_status = launch_gate.require_launch_ready()
                launch_gate.require_game_image_matches(gate_status, image_path)
            except launch_gate.LaunchGateError:
                continue
            matched = (pid, base, image_path)
            break

        if matched is None:
            time.sleep(0.10)
            continue

        pid, base, image_path = matched
        # Revalidate immediately before the memory write so a backend failure
        # during the wait cannot leave a stale PASS in effect.
        gate_status = launch_gate.require_launch_ready()
        launch_gate.require_game_image_matches(gate_status, image_path)
        print("[LAUNCH-GATE] PASS - matching TGame and live backend confirmed.")
        patch_process(pid, base)
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as exc:
        print(f"\nERROR: {exc}")
        print()
        print(
            "If this is an access-denied error, run Command Prompt / PowerShell "
            "as Administrator and run the script again."
        )
        sys.exit(1)
