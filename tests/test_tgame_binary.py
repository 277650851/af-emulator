from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCH_TOOLS = ROOT / "tools" / "patches"
if str(PATCH_TOOLS) not in sys.path:
    sys.path.insert(0, str(PATCH_TOOLS))

import tgame_binary  # noqa: E402
from tgame_test_fixtures import write_tgame_fixture  # noqa: E402


class TGameBinaryTests(unittest.TestCase):
    def test_trampoline_matches_the_verified_datetime_patch_bytes(self):
        expected = bytes.fromhex(
            "81 7C 24 04 6C 07 00 00 7D 38 "
            "C7 44 24 04 EA 07 00 00 "
            "C7 44 24 08 09 00 00 00 "
            "C7 44 24 0C 13 00 00 00 "
            "C7 44 24 10 0C 00 00 00 "
            "C7 44 24 14 00 00 00 00 "
            "C7 44 24 18 00 00 00 00 "
            "C7 44 24 1C FF FF FF FF "
            "83 EC 24 53 8B 5C 24 2C "
            "68 18 95 4B 01 C3"
        )
        self.assertEqual(tgame_binary.build_trampoline(0x014B9518), expected)

    def test_exact_target_prologue_is_accepted_when_whole_file_hash_differs(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "unpatched")
            result = tgame_binary.classify_tgame_binary(path)

        self.assertEqual(result["status"], "unpatched-compatible")
        self.assertIn("runtime patcher", result["message"])

    def test_complete_known_static_patch_is_recognized(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "patched")
            result = tgame_binary.classify_tgame_binary(path)

        self.assertEqual(result["status"], "already-patched")
        self.assertIn("complete datetime trampoline", result["message"])

    def test_position_independent_static_patch_is_accepted_with_dynamic_base(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(
                Path(temp) / "TGame.exe", "pic-patched", dynamic_base=True
            )
            result = tgame_binary.classify_tgame_binary(path)

        self.assertEqual(result["status"], "already-patched")
        self.assertIn("position-independent", result["message"])

    def test_apply_permanent_patch_creates_exact_backup_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "unpatched")
            original = path.read_bytes()
            backup = Path(str(path) + ".bak")

            result = tgame_binary.apply_static_datetime_patch(path)
            patched = path.read_bytes()
            repeated = tgame_binary.apply_static_datetime_patch(path)

            self.assertEqual(result["status"], "patched")
            self.assertEqual(backup.read_bytes(), original)
            self.assertNotEqual(patched, original)
            self.assertEqual(repeated["status"], "already-patched")
            self.assertEqual(path.read_bytes(), patched)
            self.assertEqual(
                tgame_binary.classify_tgame_binary(path)["status"], "already-patched"
            )

    def test_apply_refuses_without_code_cave_and_leaves_target_and_backup_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "unpatched")
            with tgame_binary.PE32Image(path) as image:
                section = image.section_for_rva(
                    tgame_binary.TARGET_RVA,
                    len(tgame_binary.EXPECTED_ORIGINAL),
                    executable=True,
                )
                target_offset = image.rva_to_file_offset(
                    tgame_binary.TARGET_RVA,
                    len(tgame_binary.EXPECTED_ORIGINAL),
                    executable=True,
                )
            with path.open("r+b") as stream:
                stream.seek(section.raw_pointer)
                stream.write(b"\x90" * section.raw_size)
                stream.seek(target_offset)
                stream.write(tgame_binary.EXPECTED_ORIGINAL)

            original = path.read_bytes()
            backup = Path(str(path) + ".bak")
            with self.assertRaisesRegex(tgame_binary.TGameBinaryError, "no .* code cave"):
                tgame_binary.apply_static_datetime_patch(path)

            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(backup.exists())

    def test_apply_refuses_existing_backup_for_different_original(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "unpatched")
            original = path.read_bytes()
            backup = Path(str(path) + ".bak")
            backup.write_bytes(b"different old build")

            with self.assertRaisesRegex(tgame_binary.TGameBinaryError, "does not match"):
                tgame_binary.apply_static_datetime_patch(path)

            self.assertEqual(path.read_bytes(), original)

    def test_unbacked_fixed_rva_uses_unique_clean_signature_from_executable_section(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "relocated")
            result = tgame_binary.classify_tgame_binary(path)

        self.assertEqual(result["status"], "unpatched-compatible")
        self.assertEqual(result["target_rva"], "0x00002000")
        self.assertIn("unique executable-section signature", result["message"])

    def test_unbacked_fixed_rva_without_signature_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "virtual-only")
            result = tgame_binary.classify_tgame_binary(path)

        self.assertEqual(result["status"], "unsupported")
        self.assertIn("no matching executable-section signature", result["message"])

    def test_relocated_known_trampoline_is_recognized_when_hash_differs(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "relocated-patched")
            result = tgame_binary.classify_tgame_binary(path)

        self.assertEqual(result["status"], "already-patched")
        self.assertEqual(result["target_rva"], "0x00002000")
        self.assertIn("exact datetime entry jump and trampoline", result["message"])

    def test_ambiguous_relocated_signature_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "relocated-ambiguous")
            result = tgame_binary.classify_tgame_binary(path)

        self.assertEqual(result["status"], "unsupported")
        self.assertIn("patch target is ambiguous", result["message"])

    def test_jump_without_exact_trampoline_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "bad-trampoline")
            result = tgame_binary.classify_tgame_binary(path)

        self.assertEqual(result["status"], "unsupported")
        self.assertIn("does not match", result["message"])

    def test_unknown_code_and_malformed_file_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unknown = write_tgame_fixture(root / "unknown.exe", "unknown")
            malformed = root / "malformed.exe"
            malformed.write_bytes(b"not a PE image")

            unknown_result = tgame_binary.classify_tgame_binary(unknown)
            malformed_result = tgame_binary.classify_tgame_binary(malformed)

        self.assertEqual(unknown_result["status"], "unsupported")
        self.assertIn("unexpected bytes", unknown_result["message"])
        self.assertEqual(malformed_result["status"], "unsupported")
        self.assertIn("DOS MZ header", malformed_result["message"])

    def test_cli_returns_machine_readable_patch_status(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "patched")
            result = subprocess.run(
                [sys.executable, str(PATCH_TOOLS / "tgame_binary.py"), "--json", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "already-patched")

    def test_cli_apply_writes_patch_and_machine_readable_backup_result(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(Path(temp) / "TGame.exe", "unpatched")
            original = path.read_bytes()
            result = subprocess.run(
                [
                    sys.executable,
                    str(PATCH_TOOLS / "tgame_binary.py"),
                    "--apply",
                    "--json",
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "patched")
            self.assertEqual(Path(payload["backup_path"]).read_bytes(), original)

    def test_relocatable_static_patch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = write_tgame_fixture(
                Path(temp) / "TGame.exe", "patched", dynamic_base=True
            )
            result = tgame_binary.classify_tgame_binary(path)

        self.assertEqual(result["status"], "unsupported")
        self.assertIn("relocatable image", result["message"])

    def test_runtime_patch_detection_checks_trampoline_contents(self):
        site = 0x014B9510
        continuation = site + len(tgame_binary.EXPECTED_ORIGINAL)
        trampoline = site + 0x1000
        entry = b"\xE9" + (trampoline - (site + 5)).to_bytes(4, "little", signed=True) + b"\x90\x90\x90"
        expected = tgame_binary.build_trampoline(continuation)

        self.assertTrue(
            tgame_binary.matches_runtime_patch(
                entry,
                site,
                continuation,
                lambda address, size: expected if address == trampoline and size == len(expected) else b"",
            )
        )
        static_expected = tgame_binary.build_static_trampoline(site, trampoline)
        self.assertTrue(
            tgame_binary.matches_runtime_patch(
                entry,
                site,
                continuation,
                lambda address, size: (
                    static_expected
                    if address == trampoline and size == len(static_expected)
                    else b""
                ),
            )
        )
        self.assertFalse(
            tgame_binary.matches_runtime_patch(
                entry,
                site,
                continuation,
                lambda _address, size: b"\xCC" * size,
            )
        )
        self.assertFalse(
            tgame_binary.matches_runtime_patch(
                tgame_binary.EXPECTED_ORIGINAL,
                site,
                continuation,
                lambda _address, size: b"\xCC" * size,
            )
        )


if __name__ == "__main__":
    unittest.main()
