from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCH_DIR = ROOT / "tools" / "patches"
if str(PATCH_DIR) not in sys.path:
    sys.path.insert(0, str(PATCH_DIR))

import launch_preflight_gate as gate


class LaunchPreflightGateTests(unittest.TestCase):
    def good_status(self):
        return {
            "schema": gate.PREFLIGHT_STATUS_SCHEMA,
            "server_pid": 12345,
            "passed": True,
            "log_written": True,
            "listeners_ready": True,
            "launch_ready": True,
            "checks": {name: True for name in gate.REQUIRED_CHECKS},
            "client_root": r"C:\Games\Assault Fire PH",
            "tcls_path": r"C:\Games\Assault Fire PH\TCLS\Tenio\TCLS.dll",
            "errors": [],
        }

    def write_status(self, root: Path, data: dict) -> Path:
        path = root / "preflight_status.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_pass_requires_all_checks_and_live_server(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_status(Path(td), self.good_status())
            data = gate.require_launch_ready(
                path,
                pid_alive=lambda pid: pid == 12345,
                listening_ports=lambda _pid: set(gate.REQUIRED_TCP_PORTS),
            )
            self.assertTrue(data["passed"])

    def test_exact_reported_failures_keep_launch_locked(self):
        with tempfile.TemporaryDirectory() as td:
            data = self.good_status()
            data["passed"] = False
            data["client_root"] = None
            data["tcls_path"] = None
            for name in (
                "client_root",
                "tcls_validated_build",
                "apclient_exact_bytes",
                "same_rsa_key",
            ):
                data["checks"][name] = False
            data["errors"] = [
                "client root is unknown",
                "TCLS validated build is NO",
                "APClient exact byte match is NO",
                "APClient.dat and PRIVATE.PEM same RSA key is NO",
            ]
            path = self.write_status(Path(td), data)
            with self.assertRaises(gate.LaunchGateError) as ctx:
                gate.require_launch_ready(
                    path,
                    pid_alive=lambda _pid: True,
                    listening_ports=lambda _pid: set(gate.REQUIRED_TCP_PORTS),
                )
            message = str(ctx.exception)
            self.assertIn("GAME LAUNCH BLOCKED", message)
            self.assertIn("client_root", message)
            self.assertIn("tcls_validated_build", message)
            self.assertIn("apclient_exact_bytes", message)
            self.assertIn("same_rsa_key", message)

    def test_stale_pass_from_dead_server_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_status(Path(td), self.good_status())
            with self.assertRaises(gate.LaunchGateError) as ctx:
                gate.require_launch_ready(path, pid_alive=lambda _pid: False)
            self.assertIn("server process from preflight is not running", str(ctx.exception))

    def test_missing_listener_ports_are_rejected_on_windows(self):
        from unittest import mock

        data = self.good_status()
        with mock.patch.object(gate.os, "name", "nt"):
            errors = gate.validate_status(
                data,
                pid_alive=lambda _pid: True,
                listening_ports=lambda _pid: {9060, 8000, 9010, 65005},
            )
        self.assertTrue(
            any("missing TCP port(s): 65006" in item for item in errors),
            errors,
        )

    def test_missing_status_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(gate.LaunchGateError) as ctx:
                gate.require_launch_ready(
                    Path(td) / "missing.json",
                    pid_alive=lambda _pid: True,
                    listening_ports=lambda _pid: set(gate.REQUIRED_TCP_PORTS),
                )
            self.assertIn("preflight status is missing", str(ctx.exception))

    def test_locked_listener_state_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            data = self.good_status()
            data["listeners_ready"] = False
            data["launch_ready"] = False
            path = self.write_status(Path(td), data)
            with self.assertRaises(gate.LaunchGateError) as ctx:
                gate.require_launch_ready(
                    path,
                    pid_alive=lambda _pid: True,
                    listening_ports=lambda _pid: set(gate.REQUIRED_TCP_PORTS),
                )
            self.assertIn("game launch gate is LOCKED", str(ctx.exception))

    def test_tgame_must_belong_to_preflight_client(self):
        data = self.good_status()
        gate.require_game_image_matches(
            data,
            r"C:\Games\Assault Fire PH\Binaries\Win32\TGame.exe",
        )
        with self.assertRaises(gate.LaunchGateError):
            gate.require_game_image_matches(
                data,
                r"D:\OtherClient\Binaries\Win32\TGame.exe",
            )

    def test_expected_tgame_path_translates_nt_device_path(self):
        data = self.good_status()
        data["client_root"] = (
            r"\Device\HarddiskVolume3\Program Files (x86)"
            r"\Level Up Games\Assault Fire PH"
        )

        result = gate.expected_tgame_path(
            data,
            device_map={"C:": r"\Device\HarddiskVolume1", "D:": r"\Device\HarddiskVolume3"},
        )

        self.assertEqual(
            result,
            r"D:\Program Files (x86)\Level Up Games\Assault Fire PH\Binaries\Win32\TGame.exe",
        )

    def test_expected_tgame_path_rejects_unmapped_device_path(self):
        data = self.good_status()
        data["client_root"] = r"\Device\HarddiskVolume99\Games\Assault Fire PH"

        with self.assertRaisesRegex(gate.LaunchGateError, "could not be mapped"):
            gate.expected_tgame_path(data, device_map={})

    def test_loaded_tcls_must_be_same_file_checked_by_server(self):
        data = self.good_status()
        gate.require_loaded_tcls_matches(
            data,
            r"C:\Games\Assault Fire PH\TCLS\Tenio\TCLS.dll",
        )
        with self.assertRaises(gate.LaunchGateError) as ctx:
            gate.require_loaded_tcls_matches(
                data,
                r"D:\OtherClient\TCLS\Tenio\TCLS.dll",
            )
        self.assertIn("different TCLS.dll", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
