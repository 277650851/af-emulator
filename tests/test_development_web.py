from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "server" / "development_web.py"

spec = importlib.util.spec_from_file_location("development_web_test", MOD)
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)

assert web.resolve_runtime_mode([], {}) == "development"
assert web.resolve_runtime_mode(["--development"], {}) == "development"
assert web.resolve_runtime_mode(["--production"], {}) == "production"
assert web.development_web_requested("development", [], {}) is True
assert web.development_web_requested("production", [], {"AF_DEV_WEB": "1"}) is False
assert web.development_web_requested("development", ["--no-web"], {}) is False

manager = web.DevelopmentWebProcess(
    repo_root=ROOT,
    db_path=ROOT / "server" / "test.sqlite3",
    argv=("--production",),
    env={"AF_DEV_WEB": "1"},
)
assert manager.enabled is False
assert manager.start() is False

orig_health = web._health_ok
orig_port_open = web._port_open
try:
    web._health_ok = lambda url, timeout=0.8: False
    web._port_open = lambda host, port, timeout=0.3: int(port) == 8080
    manager = web.DevelopmentWebProcess(
        repo_root=ROOT,
        db_path=ROOT / "server" / "test.sqlite3",
        argv=("--development", "--no-browser"),
        env={"AF_WEB_PORT": "8080"},
    )
    action, selected = manager._select_port()
    assert action == "spawn"
    assert selected == 8081
finally:
    web._health_ok = orig_health
    web._port_open = orig_port_open

print("DEVELOPMENT WEB TEST: PASS")
