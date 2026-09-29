"""Development-only account website process manager.

The account website is intentionally NEVER started in production mode.

Runtime mode:
  --development / AF_RUNTIME_MODE=development  -> website may auto-start
  --production  / AF_RUNTIME_MODE=production   -> website is disabled

Default mode is development because this emulator checkout is primarily a
local development/preservation workspace. Hosted deployments should always
set --production (or AF_RUNTIME_MODE=production) explicitly.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Mapping, Sequence

_TRUE = frozenset(("1", "true", "yes", "on"))
_FALSE = frozenset(("0", "false", "no", "off"))

_DEVELOPMENT = frozenset(("dev", "development", "local", "test", "testing"))
_PRODUCTION = frozenset(("prod", "production", "hosted", "live"))


class DevelopmentWebError(RuntimeError):
    pass


def resolve_runtime_mode(
    argv: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
) -> str:
    """Resolve development/production mode without importing Flask."""
    env = os.environ if env is None else env
    args = set(argv)

    dev_flag = "--development" in args or "--dev" in args
    prod_flag = "--production" in args or "--prod" in args
    if dev_flag and prod_flag:
        raise DevelopmentWebError(
            "Choose only one runtime mode: --development or --production."
        )
    if dev_flag:
        return "development"
    if prod_flag:
        return "production"

    raw = str(env.get("AF_RUNTIME_MODE") or "").strip().lower()
    if raw:
        if raw in _DEVELOPMENT:
            return "development"
        if raw in _PRODUCTION:
            return "production"
        raise DevelopmentWebError(
            "AF_RUNTIME_MODE must be development or production."
        )

    # Local preservation workspace default. Production must be explicit.
    return "development"


def development_web_requested(
    mode: str,
    argv: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
) -> bool:
    """Return True only when development mode is allowed to run the website."""
    env = os.environ if env is None else env
    if str(mode).lower() != "development":
        return False
    if "--no-web" in argv:
        return False

    raw = str(env.get("AF_DEV_WEB") or "1").strip().lower()
    if raw in _FALSE:
        return False
    return True


def browser_open_requested(
    argv: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
) -> bool:
    env = os.environ if env is None else env
    if "--no-browser" in argv:
        return False
    raw = str(env.get("AF_WEB_OPEN_BROWSER") or "1").strip().lower()
    return raw not in _FALSE


def _port_open(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _health_ok(
    url: str,
    expected_database_path: str | os.PathLike[str],
    timeout: float = 0.8,
) -> bool:
    """Identify this checkout's dev website and account database."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return False
            raw = response.read(4096)
        payload = json.loads(raw.decode("utf-8"))
        if (
            not isinstance(payload, dict)
            or payload.get("ok") is not True
            or payload.get("mode") != "development"
        ):
            return False
        reported_database = payload.get("database_path")
        if not isinstance(reported_database, str) or not reported_database:
            return False
        return Path(reported_database).resolve() == Path(
            expected_database_path
        ).resolve()
    except (
        OSError,
        UnicodeDecodeError,
        ValueError,
        urllib.error.URLError,
    ):
        return False


class DevelopmentWebProcess:
    """Launch web/app.py only for development mode and clean it up on exit."""

    def __init__(
        self,
        *,
        repo_root: str | os.PathLike[str],
        db_path: str | os.PathLike[str],
        argv: Sequence[str] = (),
        env: Mapping[str, str] | None = None,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.db_path = Path(db_path).resolve()
        self.argv = tuple(argv)
        self.env = dict(os.environ if env is None else env)
        self.mode = resolve_runtime_mode(self.argv, self.env)
        self.enabled = development_web_requested(
            self.mode, self.argv, self.env
        )
        self.process: subprocess.Popen | None = None
        self.reused_existing = False

        # Development website is loopback-only by design. Ignore web-only
        # settings when production or --no-web has disabled this subsystem.
        self.host = "127.0.0.1"
        if self.enabled:
            try:
                self.preferred_port = int(self.env.get("AF_WEB_PORT", "8080"))
            except ValueError as exc:
                raise DevelopmentWebError(
                    "AF_WEB_PORT must be an integer."
                ) from exc
            if not (1 <= self.preferred_port <= 65535):
                raise DevelopmentWebError(
                    "AF_WEB_PORT must be between 1 and 65535."
                )

            try:
                self.port_fallback_span = int(
                    self.env.get("AF_WEB_PORT_FALLBACK_SPAN", "20")
                )
            except ValueError as exc:
                raise DevelopmentWebError(
                    "AF_WEB_PORT_FALLBACK_SPAN must be an integer."
                ) from exc
            self.port_fallback_span = max(
                0, min(self.port_fallback_span, 100)
            )
            self.strict_port = (
                str(self.env.get("AF_WEB_STRICT_PORT") or "")
                .strip()
                .lower()
                in _TRUE
            )
        else:
            self.preferred_port = 8080
            self.port_fallback_span = 20
            self.strict_port = False
        self.port = self.preferred_port

        explicit_app = str(self.env.get("AF_WEB_APP") or "").strip()
        self.app_path = (
            Path(explicit_app).expanduser().resolve()
            if explicit_app
            else self.repo_root / "web" / "app.py"
        )

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def registration_url(self) -> str:
        return self.base_url + "/register"

    @property
    def login_url(self) -> str:
        return self.base_url + "/login"

    @property
    def admin_url(self) -> str:
        return self.base_url + "/admin"

    def _child_env(self) -> dict[str, str]:
        env = dict(self.env)
        env["AF_RUNTIME_MODE"] = "development"
        env["AF_WEB_HOST"] = self.host
        env["AF_WEB_PORT"] = str(self.port)
        env["AF_ACCOUNT_DB"] = str(self.db_path)
        env["PYTHONUNBUFFERED"] = "1"
        return env

    def _select_port(self) -> tuple[str, int]:
        """Choose the requested port or a safe loopback fallback."""
        preferred = int(self.preferred_port)
        health_url = f"http://{self.host}:{preferred}/healthz"

        if _health_ok(health_url, self.db_path):
            self.port = preferred
            return ("reuse", preferred)

        if not _port_open(self.host, preferred):
            self.port = preferred
            return ("spawn", preferred)

        if self.strict_port:
            raise DevelopmentWebError(
                f"Port {preferred} is already in use, but {health_url} "
                "is not the Assault Fire development website. "
                "AF_WEB_STRICT_PORT=1 prevents fallback."
            )

        last = min(65535, preferred + self.port_fallback_span)
        for candidate in range(preferred + 1, last + 1):
            candidate_health = (
                f"http://{self.host}:{candidate}/healthz"
            )
            if _health_ok(candidate_health, self.db_path):
                self.port = candidate
                return ("reuse", candidate)
            if not _port_open(self.host, candidate):
                self.port = candidate
                return ("spawn", candidate)

        raise DevelopmentWebError(
            f"Port {preferred} is busy and no free development web port "
            f"was found in {preferred + 1}-{last}. "
            "Set AF_WEB_PORT to another loopback port or increase "
            "AF_WEB_PORT_FALLBACK_SPAN."
        )

    def start(self, *, timeout: float = 15.0) -> bool:
        """Start the dev website. Return True when healthy/reused."""
        if self.mode != "development":
            print(
                "[WEB] DISABLED - production mode never starts the "
                "registration/admin website.",
                flush=True,
            )
            return False

        if not self.enabled:
            print(
                "[WEB] DISABLED - development website suppressed by "
                "--no-web / AF_DEV_WEB=0.",
                flush=True,
            )
            return False

        if not self.app_path.is_file():
            raise DevelopmentWebError(
                "Development website requested but web/app.py was not found: "
                f"{self.app_path}. Restore the existing private-repo web/ "
                "folder or set AF_WEB_APP to its app.py."
            )

        action, selected_port = self._select_port()
        if selected_port != self.preferred_port:
            print(
                f"[WEB] Preferred port {self.preferred_port} is busy; "
                f"using loopback port {selected_port} instead.",
                flush=True,
            )

        health_url = self.base_url + "/healthz"

        if action == "reuse":
            self.reused_existing = True
            print(
                f"[WEB] Reusing existing Assault Fire development website: "
                f"{self.registration_url}",
                flush=True,
            )
            self._maybe_open_browser()
            return True

        command = [sys.executable, str(self.app_path)]
        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0
            )

        self.process = subprocess.Popen(
            command,
            cwd=str(self.repo_root),
            env=self._child_env(),
            creationflags=creationflags,
        )

        deadline = time.monotonic() + max(1.0, float(timeout))
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                code = self.process.returncode
                self.process = None
                raise DevelopmentWebError(
                    f"Development website exited during startup "
                    f"(exit code {code})."
                )
            if _health_ok(health_url, self.db_path):
                print(
                    f"[WEB] Development account website ready.",
                    flush=True,
                )
                print(
                    f"[WEB] Registration: {self.registration_url}",
                    flush=True,
                )
                print(f"[WEB] Login:        {self.login_url}", flush=True)
                print(f"[WEB] Admin:        {self.admin_url}", flush=True)
                print(f"[WEB] Account DB:   {self.db_path}", flush=True)
                self._maybe_open_browser()
                return True
            time.sleep(0.15)

        self.stop()
        raise DevelopmentWebError(
            f"Development website did not become healthy within "
            f"{timeout:.1f}s at {health_url}."
        )

    def _maybe_open_browser(self) -> None:
        if not browser_open_requested(self.argv, self.env):
            return
        try:
            webbrowser.open(self.registration_url, new=2)
        except Exception as exc:
            print(
                f"[WEB] Browser auto-open failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

    def stop(self) -> None:
        if self.reused_existing:
            # We did not create it, so never terminate it.
            return
        proc = self.process
        self.process = None
        if proc is None or proc.poll() is not None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=3.0)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
