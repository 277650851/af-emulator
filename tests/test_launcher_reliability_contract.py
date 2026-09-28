from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "START_ASSAULT_FIRE.ps1"
HELPER = ROOT / "tools" / "patches" / "patch_tcls_suspended_launch.py"


class LauncherReliabilityContractTests(unittest.TestCase):
    def test_launcher_relaunches_elevated_before_initializing_or_mutating(self):
        source = SCRIPT.read_text(encoding="utf-8", errors="replace")
        self.assertIn("$currentPowerShellExe", source)
        self.assertIn("Start-Process -FilePath $currentPowerShellExe -Verb RunAs", source)
        self.assertLess(source.index("Start-Process -FilePath $currentPowerShellExe"), source.index("Initialize-LauncherConfig"))
        for switch in ("SetupOnly", "SkipPythonInstall", "KeepServer"):
            self.assertIn(f'if (${switch})', source)

    def test_elevated_entrypoint_does_not_prompt_again_for_child_processes(self):
        source = SCRIPT.read_text(encoding="utf-8", errors="replace")
        self.assertEqual(source.count("-Verb RunAs"), 1)
        self.assertNotIn("Administrator permission is required for the server runtime", source)
        self.assertNotIn("Administrator permission is required for the TGame launch helper", source)

    def test_helper_arming_uses_log_marker_not_uac_wrapper_exit_code(self):
        source = SCRIPT.read_text(encoding="utf-8", errors="replace")
        start = source.index("function Wait-ForTclsHelperArmed")
        end = source.index("Initialize-LauncherConfig", start)
        wait_body = source[start:end]
        self.assertIn("TCLS ARMED", wait_body)
        self.assertIn("$HelperProcess.ExitCode -ne 0", wait_body)
        self.assertNotIn("if ($HelperProcess.HasExited) {", wait_body)

    def test_launcher_waits_for_verified_patch_and_resume_before_success(self):
        source = SCRIPT.read_text(encoding="utf-8", errors="replace")
        self.assertIn("function Wait-ForTgameHelperComplete", source)
        wait_call = source.index("Wait-ForTgameHelperComplete $helperLog")
        success = source.index('[SUCCESS] TGame.exe launched.')
        self.assertLess(wait_call, success)

    def test_helper_logs_datetime_patch_and_resume_markers(self):
        source = HELPER.read_text(encoding="utf-8", errors="replace")
        self.assertIn("[AF-DATETIME-PATCHED]", source)
        self.assertIn("[AF-TGAME-RESUMED]", source)


if __name__ == "__main__":
    unittest.main()
