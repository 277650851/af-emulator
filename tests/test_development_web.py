from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest import mock

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
    env={"AF_DEV_WEB": "1", "AF_WEB_PORT": "not-a-port"},
)
assert manager.enabled is False
assert manager.start() is False

orig_health = web._health_ok
orig_port_open = web._port_open
try:
    web._health_ok = lambda url, _db_path, timeout=0.8: False
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


class _FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return json.dumps(self.payload).encode("utf-8")


def test_health_check_requires_development_mode_and_database_identity():
    expected_db = ROOT / "server" / "accounts.sqlite3"
    url = "http://127.0.0.1:8080/healthz"
    payloads = (
        {"ok": True},
        {
            "ok": True,
            "mode": "development",
            "database_path": str(ROOT / "other" / "accounts.sqlite3"),
        },
        {
            "ok": True,
            "mode": "development",
            "database_path": str(expected_db),
        },
    )
    results = []
    for payload in payloads:
        with mock.patch.object(
            web.urllib.request,
            "urlopen",
            return_value=_FakeResponse(payload),
        ):
            results.append(web._health_ok(url, expected_db))
    assert results == [False, False, True]


test_health_check_requires_development_mode_and_database_identity()

server_source = (ROOT / "server" / "assaultfire_server_v143b.py").read_text(
    encoding="utf-8"
)
bind_failure = server_source[
    server_source.index("except Exception as bind_exc:"):server_source.index(
        "# Normal local-client mode keeps the strict launch gate."
    )
]
assert "_development_web.stop()" in bind_failure

print("DEVELOPMENT WEB TEST: PASS")
