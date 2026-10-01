"""Durable, expiring server-side state for TGame authentication sessions.

AUTH tickets are short-lived and bound to the authenticated UIN and client IP.
The AES keys are encrypted in SQLite with a key derived from the stable server
RSA private key, so a process restart can recover an unexpired session without
writing plaintext crypto keys to disk.  The database and PRIVATE.PEM must both
be kept private and backed up together if sessions are expected to survive a
host restart.
"""

from __future__ import annotations

import ipaddress
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

TICKET_TTL_SECONDS = 300
DEFAULT_SESSION_TTL_SECONDS = 900
try:
    SESSION_TTL_SECONDS = max(
        60,
        min(
            7 * 24 * 60 * 60,
            int(os.environ.get(
                "AF_TGAME_SESSION_TTL_SECONDS",
                str(DEFAULT_SESSION_TTL_SECONDS),
            )),
        ),
    )
except (TypeError, ValueError):
    SESSION_TTL_SECONDS = DEFAULT_SESSION_TTL_SECONDS

_TICKET_RE = frozenset("0123456789ABCDEF")
_DB_PATH = Path(
    os.environ.get(
        "AF_ACCOUNT_DB",
        str(Path(__file__).with_name("assaultfire_accounts.sqlite3")),
    )
)
_DEFAULT_PRIVATE_KEY_PATH = Path(__file__).with_name("PRIVATE.PEM")
_KEY_DERIVATION_SALT = b"AssaultFire/TGame/session-store/v1"
_KEY_DERIVATION_INFO = b"SQLite AEAD key derived from server RSA private key"


def _ip(value: str | None) -> str | None:
    if not value:
        return None
    try:
        address = ipaddress.ip_address(str(value).strip())
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        return str(address)
    except ValueError:
        return None


def _ticket_text(ticket: bytes | str) -> str | None:
    try:
        value = ticket.decode("ascii", "strict") if isinstance(ticket, bytes) else str(ticket)
    except UnicodeDecodeError:
        return None
    if len(value) != 16 or any(character not in _TICKET_RE for character in value):
        return None
    return value


def _path(db_path: str | os.PathLike[str] | None = None) -> Path:
    return Path(db_path) if db_path is not None else _DB_PATH


def _private_key_path(
    private_key_path: str | os.PathLike[str] | None = None,
) -> Path:
    if private_key_path is not None:
        return Path(private_key_path)
    return Path(os.environ.get("AF_PRIVATE_KEY", str(_DEFAULT_PRIVATE_KEY_PATH)))


def _storage_cipher(
    private_key_path: str | os.PathLike[str] | None = None,
) -> AESGCM:
    key_path = _private_key_path(private_key_path)
    try:
        key_material = key_path.read_bytes()
    except OSError as exc:
        raise RuntimeError(
            "Cannot open the server PRIVATE.PEM needed to encrypt persisted "
            "TGame sessions"
        ) from exc
    if len(key_material) < 64:
        raise RuntimeError("Server PRIVATE.PEM is too short for session encryption")
    key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_KEY_DERIVATION_SALT,
        info=_KEY_DERIVATION_INFO,
    ).derive(key_material)
    return AESGCM(key)


def _aad(ticket: str, uin: int, client_ip: str, purpose: str, mode: int) -> bytes:
    return (
        f"af-tgame-session-v1|{ticket}|{int(uin)}|{client_ip}|{purpose}|{int(mode)}"
    ).encode("ascii")


def _encrypt_key(
    key: bytes,
    *,
    ticket: str,
    uin: int,
    client_ip: str,
    purpose: str,
    mode: int,
    private_key_path: str | os.PathLike[str] | None = None,
) -> bytes:
    if len(key) != 16:
        raise ValueError("TGame AES keys must be exactly 16 bytes")
    nonce = secrets.token_bytes(12)
    return nonce + _storage_cipher(private_key_path).encrypt(
        nonce,
        key,
        _aad(ticket, uin, client_ip, purpose, mode),
    )


def _decrypt_key(
    value: bytes,
    *,
    ticket: str,
    uin: int,
    client_ip: str,
    purpose: str,
    mode: int,
    private_key_path: str | os.PathLike[str] | None = None,
) -> bytes:
    value = bytes(value)
    if len(value) != 12 + 16 + 16:
        raise ValueError("invalid encrypted TGame key length")
    return _storage_cipher(private_key_path).decrypt(
        value[:12],
        value[12:],
        _aad(ticket, uin, client_ip, purpose, mode),
    )


def _connect(db_path: str | os.PathLike[str] | None = None) -> sqlite3.Connection:
    path = _path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _init_db(db_path: str | os.PathLike[str] | None = None) -> None:
    conn = _connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS af_tgame_sessions (
                ticket TEXT PRIMARY KEY,
                uin INTEGER NOT NULL CHECK (uin > 0),
                client_ip TEXT NOT NULL,
                auth_key_enc BLOB NOT NULL,
                transport_key_enc BLOB,
                key_mode INTEGER NOT NULL CHECK (key_mode IN (3, 4)),
                state TEXT NOT NULL DEFAULT 'ticket_issued'
                    CHECK (state IN ('ticket_issued', 'transport_ready')),
                created_at REAL NOT NULL,
                last_seen_at REAL NOT NULL,
                ticket_expires_at REAL NOT NULL,
                expires_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_af_tgame_sessions_ip_expiry
                ON af_tgame_sessions(client_ip, expires_at DESC);
            CREATE INDEX IF NOT EXISTS idx_af_tgame_sessions_expiry
                ON af_tgame_sessions(expires_at);
            """
        )
        conn.commit()
    finally:
        conn.close()


def _prune_expired(conn: sqlite3.Connection, now: float) -> None:
    conn.execute("DELETE FROM af_tgame_sessions WHERE expires_at <= ?", (now,))


def issue_ticket(
    uin: int,
    client_ip: str | None,
    auth_key: bytes,
    *,
    mode: int = 3,
    ttl_seconds: int = TICKET_TTL_SECONDS,
    session_ttl_seconds: int = SESSION_TTL_SECONDS,
    db_path: str | os.PathLike[str] | None = None,
    private_key_path: str | os.PathLike[str] | None = None,
) -> bytes:
    """Create a wire ticket and persist its encrypted AUTH/session state."""
    normalized_ip = _ip(client_ip)
    key = bytes(auth_key)
    numeric_uin = int(uin)
    numeric_mode = int(mode)
    if normalized_ip is None:
        raise ValueError("Cannot issue a TGame ticket without a valid client IP")
    if numeric_uin <= 0 or numeric_uin > 0xFFFFFFFF:
        raise ValueError("Cannot issue a TGame ticket without a valid UIN")
    if len(key) != 16:
        raise ValueError("AUTH key must be exactly 16 bytes")
    if numeric_mode not in (3, 4):
        raise ValueError("TGame key mode must be 3 or 4")
    ttl = float(ttl_seconds)
    session_ttl = float(session_ttl_seconds)
    if ttl <= 0:
        raise ValueError("Ticket lifetime must be positive")
    if session_ttl <= 0:
        raise ValueError("Session lifetime must be positive")

    now = time.time()
    ticket_expires_at = now + ttl
    expires_at = now + session_ttl
    _init_db(db_path)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _prune_expired(conn, now)
        ticket = secrets.token_hex(8).upper()
        while conn.execute(
            "SELECT 1 FROM af_tgame_sessions WHERE ticket = ?", (ticket,)
        ).fetchone():
            ticket = secrets.token_hex(8).upper()
        auth_key_enc = _encrypt_key(
            key,
            ticket=ticket,
            uin=numeric_uin,
            client_ip=normalized_ip,
            purpose="auth",
            mode=numeric_mode,
            private_key_path=private_key_path,
        )
        conn.execute(
            """INSERT INTO af_tgame_sessions(
                   ticket, uin, client_ip, auth_key_enc, transport_key_enc,
                   key_mode, state, created_at, last_seen_at,
                   ticket_expires_at, expires_at
               ) VALUES (?, ?, ?, ?, NULL, ?, 'ticket_issued', ?, ?, ?, ?)""",
            (
                ticket,
                numeric_uin,
                normalized_ip,
                auth_key_enc,
                numeric_mode,
                now,
                now,
                ticket_expires_at,
                expires_at,
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return ticket.encode("ascii")


def get_ticket_crypto(
    ticket: bytes | str,
    uin: int,
    client_ip: str | None,
    *,
    db_path: str | os.PathLike[str] | None = None,
    private_key_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any] | None:
    """Recover an unexpired AUTH key across processes, bound to UIN and IP."""
    ticket_text = _ticket_text(ticket)
    normalized_ip = _ip(client_ip)
    try:
        numeric_uin = int(uin)
    except (TypeError, ValueError):
        return None
    if ticket_text is None or normalized_ip is None or numeric_uin <= 0:
        return None

    now = time.time()
    _init_db(db_path)
    conn = _connect(db_path)
    try:
        _prune_expired(conn, now)
        row = conn.execute(
            """SELECT auth_key_enc, key_mode, ticket_expires_at, expires_at,
                      state, created_at, last_seen_at
               FROM af_tgame_sessions
               WHERE ticket = ? AND uin = ? AND client_ip = ?
                 AND ticket_expires_at > ? AND expires_at > ?""",
            (ticket_text, numeric_uin, normalized_ip, now, now),
        ).fetchone()
        if row is None:
            conn.commit()
            return None
        mode = int(row["key_mode"])
        try:
            auth_key = _decrypt_key(
                row["auth_key_enc"],
                ticket=ticket_text,
                uin=numeric_uin,
                client_ip=normalized_ip,
                purpose="auth",
                mode=mode,
                private_key_path=private_key_path,
            )
        except Exception:
            # A changed server private key makes old rows unreadable. Delete
            # only this unusable ticket; subsequent logins can issue a new one.
            conn.execute(
                "DELETE FROM af_tgame_sessions WHERE ticket = ?", (ticket_text,)
            )
            conn.commit()
            return None
        conn.commit()
        return {
            "uin": numeric_uin,
            "client_ip": normalized_ip,
            "session_key": auth_key,
            "mode": mode,
            "ticket": ticket_text,
            "state": str(row["state"]),
            "created_at": float(row["created_at"]),
            "last_seen_at": float(row["last_seen_at"]),
            "ticket_expires_at": float(row["ticket_expires_at"]),
            "expires_at": float(row["expires_at"]),
        }
    finally:
        conn.close()


def save_transport_key(
    ticket: bytes | str,
    uin: int,
    client_ip: str | None,
    transport_key: bytes,
    *,
    mode: int = 3,
    ttl_seconds: int = SESSION_TTL_SECONDS,
    db_path: str | os.PathLike[str] | None = None,
    private_key_path: str | os.PathLike[str] | None = None,
) -> bool:
    """Persist the post-CHGSKEY transport key and refresh the session expiry."""
    ticket_text = _ticket_text(ticket)
    normalized_ip = _ip(client_ip)
    numeric_uin = int(uin)
    numeric_mode = int(mode)
    key = bytes(transport_key)
    if ticket_text is None or normalized_ip is None:
        return False
    if numeric_uin <= 0 or numeric_mode not in (3, 4):
        return False
    if len(key) != 16:
        raise ValueError("transport key must be exactly 16 bytes")
    ttl = float(ttl_seconds)
    if ttl <= 0:
        raise ValueError("Session lifetime must be positive")

    now = time.time()
    key_enc = _encrypt_key(
        key,
        ticket=ticket_text,
        uin=numeric_uin,
        client_ip=normalized_ip,
        purpose="transport",
        mode=numeric_mode,
        private_key_path=private_key_path,
    )
    _init_db(db_path)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        _prune_expired(conn, now)
        result = conn.execute(
            """UPDATE af_tgame_sessions
               SET transport_key_enc = ?, key_mode = ?, state = 'transport_ready',
                   last_seen_at = ?, expires_at = ?
               WHERE ticket = ? AND uin = ? AND client_ip = ? AND expires_at > ?""",
            (
                key_enc,
                numeric_mode,
                now,
                now + ttl,
                ticket_text,
                numeric_uin,
                normalized_ip,
                now,
            ),
        )
        conn.commit()
        return result.rowcount == 1
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_sessions_for_ip(
    client_ip: str | None,
    *,
    db_path: str | os.PathLike[str] | None = None,
    private_key_path: str | os.PathLike[str] | None = None,
) -> list[dict[str, Any]]:
    """Return unexpired sessions for reconnect matching, newest activity first.

    Callers must still disambiguate multiple accounts behind the same public
    IP. The IP is a lookup constraint, not proof of account identity.
    """
    normalized_ip = _ip(client_ip)
    if normalized_ip is None:
        return []
    now = time.time()
    _init_db(db_path)
    conn = _connect(db_path)
    try:
        _prune_expired(conn, now)
        rows = conn.execute(
            """SELECT ticket, uin, client_ip, transport_key_enc,
                      key_mode, state, created_at, last_seen_at, expires_at
               FROM af_tgame_sessions
               WHERE client_ip = ? AND state = 'transport_ready'
                 AND transport_key_enc IS NOT NULL AND expires_at > ?
               ORDER BY last_seen_at DESC""",
            (normalized_ip, now),
        ).fetchall()
        sessions = []
        for row in rows:
            ticket = str(row["ticket"])
            uin = int(row["uin"])
            mode = int(row["key_mode"])
            common = {
                "ticket": ticket,
                "uin": uin,
                "client_ip": normalized_ip,
                "mode": mode,
                "state": str(row["state"]),
                "created_at": float(row["created_at"]),
                "last_seen_at": float(row["last_seen_at"]),
                "expires_at": float(row["expires_at"]),
            }
            try:
                transport_key_enc = row["transport_key_enc"]
                common["transport_key"] = (
                    _decrypt_key(
                        transport_key_enc,
                        ticket=ticket,
                        uin=uin,
                        client_ip=normalized_ip,
                        purpose="transport",
                        mode=mode,
                        private_key_path=private_key_path,
                    )
                    if transport_key_enc is not None
                    else None
                )
            except Exception:
                conn.execute(
                    "DELETE FROM af_tgame_sessions WHERE ticket = ?", (ticket,)
                )
                continue
            sessions.append(common)
        conn.commit()
        return sessions
    finally:
        conn.close()


def get_unexpired_session_uins(
    *,
    db_path: str | os.PathLike[str] | None = None,
) -> set[int]:
    """Return UINs with a live persisted transport session, without keys."""
    now = time.time()
    _init_db(db_path)
    conn = _connect(db_path)
    try:
        _prune_expired(conn, now)
        rows = conn.execute(
            """SELECT DISTINCT uin FROM af_tgame_sessions
               WHERE state = 'transport_ready'
                 AND transport_key_enc IS NOT NULL AND expires_at > ?""",
            (now,),
        ).fetchall()
        conn.commit()
        return {int(row["uin"]) for row in rows}
    finally:
        conn.close()


def touch_session(
    ticket: bytes | str,
    uin: int,
    client_ip: str | None,
    *,
    ttl_seconds: int = SESSION_TTL_SECONDS,
    db_path: str | os.PathLike[str] | None = None,
) -> bool:
    """Slide the idle expiry after valid traffic from the bound live session."""
    ticket_text = _ticket_text(ticket)
    normalized_ip = _ip(client_ip)
    if ticket_text is None or normalized_ip is None or int(uin) <= 0:
        return False
    ttl = float(ttl_seconds)
    if ttl <= 0:
        return False
    now = time.time()
    _init_db(db_path)
    conn = _connect(db_path)
    try:
        _prune_expired(conn, now)
        result = conn.execute(
            """UPDATE af_tgame_sessions
               SET last_seen_at = ?, expires_at = ?
               WHERE ticket = ? AND uin = ? AND client_ip = ? AND expires_at > ?""",
            (now, now + ttl, ticket_text, int(uin), normalized_ip, now),
        )
        conn.commit()
        return result.rowcount == 1
    finally:
        conn.close()


def delete_session(
    ticket: bytes | str,
    *,
    db_path: str | os.PathLike[str] | None = None,
) -> bool:
    """Revoke one persisted TGame session immediately."""
    ticket_text = _ticket_text(ticket)
    if ticket_text is None:
        return False
    _init_db(db_path)
    conn = _connect(db_path)
    try:
        result = conn.execute(
            "DELETE FROM af_tgame_sessions WHERE ticket = ?", (ticket_text,)
        )
        conn.commit()
        return result.rowcount == 1
    finally:
        conn.close()
