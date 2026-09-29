from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ServerCleanImportTests(unittest.TestCase):
    def test_server_module_imports_from_clean_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            env = os.environ.copy()
            env.update(
                {
                    "AF_ACCOUNT_DB": str(Path(td) / "accounts.sqlite3"),
                    "AF_RUNTIME_MODE": "production",
                    "AF_DEV_WEB": "0",
                }
            )
            result = subprocess.run(
                [sys.executable, "-c", "import assaultfire_server_v143b"],
                cwd=ROOT / "server",
                env=env,
                text=True,
                capture_output=True,
                timeout=30,
            )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"server import failed:\n{result.stdout}\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
