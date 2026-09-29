from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "web" / "app.py"

with tempfile.TemporaryDirectory() as td:
    os.environ["AF_ACCOUNT_DB"] = str(Path(td) / "accounts.sqlite3")
    os.environ["AF_ADMIN_USERNAME"] = "admin"
    os.environ["AF_ADMIN_PASSWORD"] = "test-admin-password"

    spec = importlib.util.spec_from_file_location("af_dev_web_app_test", APP_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    client = mod.app.test_client()

    assert client.get("/register").status_code == 200
    assert client.get("/login").status_code == 200
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.json["database_path"] == str(mod.DB_PATH)
    assert client.get("/admin").status_code == 404

    with client.session_transaction() as sess:
        sess["_csrf"] = "token"
    too_short = client.post(
        "/register",
        data={
            "csrf_token": "token",
            "username": "ab",
            "password": "password1",
            "confirm_password": "password1",
        },
    )
    assert too_short.status_code == 200
    assert b"3-24 characters" in too_short.data

    legacy_length = client.post(
        "/register",
        data={
            "csrf_token": "token",
            "username": "lmao",
            "password": "password1",
            "confirm_password": "password1",
        },
    )
    assert legacy_length.status_code == 200
    assert b"Registration complete" in legacy_length.data

print("DEVELOPMENT WEB ROUTE TEST: PASS")
