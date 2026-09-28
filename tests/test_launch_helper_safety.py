from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LaunchHelperStaticSafetyTests(unittest.TestCase):
    def test_suspended_helper_requires_direct_child_and_rechecks_gate(self):
        source = (ROOT / "tools" / "patches" / "patch_tcls_suspended_launch.py").read_text(
            encoding="utf-8", errors="replace"
        )
        self.assertNotIn("(children or candidates)[0]", source)
        self.assertIn('row["ppid"] == parent_pid', source)
        self.assertIn("require_game_image_matches", source)
        self.assertIn("wait_for_module(hclient, TCLS_MODULE, 120.0)", source)
        self.assertIn("target_rva_for_image(game_path)", source)
        self.assertIn("patch_process(game_pid, game_base, target_rva)", source)
        patch_call = source.index("datetime_patch.patch_process(game_pid, game_base, target_rva)")
        patched_marker = source.index("[AF-DATETIME-PATCHED]")
        resume_call = source.index("resume_primary_thread(game_pid)")
        resumed_marker = source.index("[AF-TGAME-RESUMED]")
        self.assertLess(patch_call, patched_marker)
        self.assertLess(patched_marker, resume_call)
        self.assertLess(resume_call, resumed_marker)
        self.assertGreaterEqual(source.count("require_launch_ready()"), 4)

    def test_datetime_helper_ignores_existing_tgame_and_checks_image_path(self):
        source = (ROOT / "tools" / "patches" / "patch_tgame_datetime.py").read_text(
            encoding="utf-8", errors="replace"
        )
        self.assertIn("existing_pids = set(find_processes(PROCESS_NAME))", source)
        self.assertIn("pid not in existing_pids", source)
        self.assertIn("require_game_image_matches", source)
        self.assertIn("matches_runtime_patch", source)
        self.assertIn("target_rva_for_image(image_path)", source)
        self.assertIn("patch_process(pid, base, target_rva)", source)
        self.assertIn("PATCHED (already active)", source)
        self.assertGreaterEqual(source.count("require_launch_ready()"), 2)


    def test_datetime_patch_protects_and_restores_the_tgame_entry_page(self):
        source = (ROOT / "tools" / "patches" / "patch_tgame_datetime.py").read_text(
            encoding="utf-8", errors="replace"
        )
        protect = source.index('winerr("VirtualProtectEx(make TGame entry writable)")')
        entry_write = source.index("write_memory(process, target, entry_patch)")
        restore = source.index(
            'winerr("VirtualProtectEx(restore TGame entry protection)")'
        )

        self.assertIn("kernel32.VirtualProtectEx.argtypes", source)
        self.assertIn("PAGE_EXECUTE_READWRITE", source)
        self.assertLess(protect, entry_write)
        self.assertLess(entry_write, restore)
        self.assertIn("finally:", source[entry_write:restore])
        self.assertIn("entry_page_protection.value", source)
        self.assertIn('winerr("FlushInstructionCache(TGame entry)")', source)

if __name__ == "__main__":
    unittest.main()
