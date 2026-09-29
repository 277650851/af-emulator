"""Local one-shot first-account setup for the Assault Fire PH emulator.

This module is deliberately small and dependency-free. It reuses account_db.py
for validation, password hashing, SQLite schema creation, and shared UIN allocation.
It never assigns a game nickname; new accounts keep nickname = NULL.
"""

from __future__ import annotations

import html
import os
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from account_db import (
    DEFAULT_DB_PATH,
    AccountError,
    account_count,
    create_account,
)

_TRUE = frozenset(("1", "true", "yes", "on"))


def _env_true(name: str) -> bool:
    return (os.environ.get(name) or "").strip().lower() in _TRUE


def needs_first_run(db_path: str | os.PathLike[str] | None = None) -> bool:
    """True only when there is no DB yet, or the existing DB has zero accounts."""
    path = Path(db_path) if db_path is not None else Path(DEFAULT_DB_PATH)
    if not path.exists():
        return True
    return account_count(db_path=path) == 0


def register_first_account(
    username: str,
    password: str,
    confirm_password: str,
    *,
    db_path: str | os.PathLike[str] | None = None,
) -> dict:
    if password != confirm_password:
        raise AccountError("Passwords do not match.")
    # Authoritative account path: PBKDF2 hashing, validation, shared UIN allocation,
    # profiles.nickname = NULL.
    return create_account(username, password, db_path=db_path)


def _page(*, csrf: str, error: str = "", success: dict | None = None) -> str:
    if success is not None:
        username = html.escape(str(success["username"]))
        uin = html.escape(str(success["uin"]))
        body = f"""
        <main class="card">
          <h1>Account created</h1>
          <p><strong>{username}</strong> was created with UIN <strong>{uin}</strong>.</p>
          <p>The game nickname is still <strong>unset</strong>. This is intentional.</p>
          <p>The setup website is closing. Server startup will continue automatically.</p>
        </main>
        """
    else:
        error_box = (
            f'<div class="error">{html.escape(error)}</div>' if error else ""
        )
        body = f"""
        <main class="card">
          <h1>Assault Fire PH</h1>
          <p class="muted">First-time server setup</p>
          {error_box}
          <form method="post" action="/register" autocomplete="off">
            <input type="hidden" name="csrf" value="{html.escape(csrf)}">
            <label for="username">Username</label>
            <input id="username" name="username" minlength="3" maxlength="24"
                   pattern="[A-Za-z0-9._-]+" required autofocus>
            <label for="password">Password</label>
            <input id="password" type="password" name="password"
                   minlength="8" maxlength="72" required>
            <label for="confirm_password">Confirm password</label>
            <input id="confirm_password" type="password" name="confirm_password"
                   minlength="8" maxlength="72" required>
            <button type="submit">Create account</button>
          </form>
          <p class="muted small">
            Your nickname is created later by the stock game client on first login.
          </p>
        </main>
        """

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Assault Fire PH - First Setup</title>
<style>
:root {{ color-scheme:dark; font-family:"Segoe UI",Arial,sans-serif; }}
body {{ margin:0; min-height:100vh; display:grid; place-items:center;
        background:#10151e; color:#f2f5f8; }}
.card {{ box-sizing:border-box; width:min(440px,calc(100vw - 36px));
         padding:28px; border:1px solid #303b4d; border-radius:14px;
         background:#1a2230; box-shadow:0 20px 55px rgba(0,0,0,.38); }}
h1 {{ margin:0 0 8px; font-size:26px; }}
.muted {{ color:#aeb8c7; }}
.small {{ font-size:13px; line-height:1.45; }}
label {{ display:block; margin:15px 0 6px; font-weight:600; }}
input {{ box-sizing:border-box; width:100%; padding:11px 12px;
         border:1px solid #46546c; border-radius:8px;
         background:#101722; color:#fff; font-size:15px; }}
button {{ width:100%; margin-top:20px; padding:12px; border:0;
          border-radius:8px; font-size:15px; font-weight:700; cursor:pointer; }}
.error {{ margin:14px 0; padding:10px 12px; border:1px solid #7d3d48;
          border-radius:8px; background:#3b2026; }}
</style>
</head>
<body>{body}</body>
</html>"""


class _SetupHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address,
        *,
        db_path: Path,
        csrf: str,
        completed: threading.Event,
    ):
        super().__init__(server_address, _SetupHandler)
        self.db_path = db_path
        self.csrf = csrf
        self.completed = completed


class _SetupHandler(BaseHTTPRequestHandler):
    server_version = "AF-FirstRun/1.0"

    def log_message(self, fmt: str, *args) -> None:
        # Never log POST bodies or passwords.
        print("[FIRST-RUN-WEB] " + (fmt % args))

    def _html(self, status: int, page: str) -> None:
        raw = page.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; "
            "form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self._html(404, _page(csrf=self.server.csrf, error="Page not found."))
            return
        self._html(200, _page(csrf=self.server.csrf))

    def do_POST(self) -> None:
        if self.path != "/register":
            self._html(404, _page(csrf=self.server.csrf, error="Page not found."))
            return

        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = 0

        if size <= 0 or size > 4096:
            self._html(
                400,
                _page(csrf=self.server.csrf, error="Invalid form submission."),
            )
            return

        form = parse_qs(
            self.rfile.read(size).decode("utf-8", "replace"),
            keep_blank_values=True,
        )

        submitted_csrf = (form.get("csrf") or [""])[0]
        if not secrets.compare_digest(submitted_csrf, self.server.csrf):
            self._html(
                403,
                _page(
                    csrf=self.server.csrf,
                    error="Setup session expired. Refresh the page.",
                ),
            )
            return

        username = (form.get("username") or [""])[0]
        password = (form.get("password") or [""])[0]
        confirm = (form.get("confirm_password") or [""])[0]

        try:
            account = register_first_account(
                username,
                password,
                confirm,
                db_path=self.server.db_path,
            )
        except AccountError as exc:
            self._html(400, _page(csrf=self.server.csrf, error=str(exc)))
            return
        except Exception as exc:
            print(
                "[FIRST-RUN-WEB] account creation failed: "
                f"{type(exc).__name__}: {exc}"
            )
            self._html(
                500,
                _page(
                    csrf=self.server.csrf,
                    error="Account creation failed. Check the server console.",
                ),
            )
            return

        print(
            "[FIRST-RUN] account created "
            f"username={account['username']!r} "
            f"uin={account['uin']} nickname=NULL"
        )
        self._html(200, _page(csrf=self.server.csrf, success=account))
        self.server.completed.set()


def _create_httpd(db_path: Path) -> tuple[_SetupHTTPServer, str]:
    explicit_port = "AF_FIRST_RUN_PORT" in os.environ
    raw_port = (os.environ.get("AF_FIRST_RUN_PORT") or "8765").strip()
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise RuntimeError("AF_FIRST_RUN_PORT must be an integer.") from exc

    if not (0 <= port <= 65535):
        raise RuntimeError("AF_FIRST_RUN_PORT must be between 0 and 65535.")

    completed = threading.Event()
    csrf = secrets.token_urlsafe(32)

    try:
        httpd = _SetupHTTPServer(
            ("127.0.0.1", port),
            db_path=db_path,
            csrf=csrf,
            completed=completed,
        )
    except OSError:
        if explicit_port:
            raise
        # The default port is only a convenience. Stay loopback-only and use a
        # free ephemeral port if 8765 is already occupied.
        httpd = _SetupHTTPServer(
            ("127.0.0.1", 0),
            db_path=db_path,
            csrf=csrf,
            completed=completed,
        )

    actual_port = int(httpd.server_address[1])
    return httpd, f"http://127.0.0.1:{actual_port}/"


def ensure_first_account(
    db_path: str | os.PathLike[str] | None = None,
) -> bool:
    """Run first-account setup if needed.

    Returns True if setup was shown and an account was created, False when an
    existing account was already present or the gate was explicitly skipped.
    """
    path = (
        Path(db_path).expanduser().resolve()
        if db_path is not None
        else Path(DEFAULT_DB_PATH).expanduser().resolve()
    )

    if _env_true("AF_SKIP_FIRST_RUN_SETUP"):
        print("[FIRST-RUN] setup gate skipped by AF_SKIP_FIRST_RUN_SETUP")
        return False

    try:
        required = needs_first_run(path)
    except Exception as exc:
        raise RuntimeError(
            f"Cannot read account database {path}; refusing to replace/reset it."
        ) from exc

    if not required:
        print(f"[FIRST-RUN] existing account database found: {path}")
        return False

    httpd, url = _create_httpd(path)
    worker = threading.Thread(
        target=httpd.serve_forever,
        name="AF-first-run-web",
        daemon=True,
    )
    worker.start()

    print("=" * 72)
    print("[FIRST-RUN] No registered accounts were found.")
    print(f"[FIRST-RUN] Account DB : {path}")
    print(f"[FIRST-RUN] Setup URL  : {url}")
    print("[FIRST-RUN] Waiting for the first website account...")
    print("=" * 72)

    if not _env_true("AF_FIRST_RUN_NO_BROWSER"):
        try:
            opened = webbrowser.open(url, new=1, autoraise=True)
            if not opened:
                print("[FIRST-RUN] Browser did not report success; open the URL above.")
        except Exception as exc:
            print(f"[FIRST-RUN] Could not open browser automatically: {exc}")

    try:
        httpd.completed.wait()
    except KeyboardInterrupt:
        print("\n[FIRST-RUN] setup cancelled")
        raise
    finally:
        httpd.shutdown()
        httpd.server_close()
        worker.join(timeout=2.0)

    print("[FIRST-RUN] First account ready. Continuing normal server startup.")
    return True


if __name__ == "__main__":
    ensure_first_account()
