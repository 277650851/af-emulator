"""PH AP credential parsing and account verification helpers."""

from __future__ import annotations

import re
import struct
import time
from pathlib import Path
from typing import Any

try:
    from .account_db import verify_ap_credential
except ImportError:  # Loaded as a sibling module by the server script.
    from account_db import verify_ap_credential


_AP_TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")
_MAX_TDR_STRING_BYTES = 129


def _read_nul_terminated_string(
    body: bytes,
    offset: int,
    *,
    label: str,
    encoding: str,
) -> tuple[str, int]:
    if offset + 4 > len(body):
        raise ValueError(f"AP verify body missing {label} length")

    length = struct.unpack_from(">I", body, offset)[0]
    offset += 4
    if (
        length < 2
        or length > _MAX_TDR_STRING_BYTES
        or offset + length > len(body)
    ):
        raise ValueError(f"invalid AP {label} length {length}")

    raw = body[offset:offset + length]
    if raw[-1:] != b"\x00":
        raise ValueError(f"AP {label} is missing its trailing NUL")

    try:
        value = raw[:-1].decode(encoding, "strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"AP {label} has invalid {encoding} encoding") from exc
    return value, offset + length


def parse_ap_verify_credentials(body: bytes) -> tuple[str, str]:
    """Parse the PH AP_CMD_VERIFY username and 32-hex password token."""
    body = bytes(body or b"")
    if len(body) < 2:
        raise ValueError("AP verify body is too short")

    # The first two bytes are the inner-size scalar. Its observed value varies
    # with string lengths, so parse the fixed-width fields that follow it.
    username, offset = _read_nul_terminated_string(
        body,
        2,
        label="login name",
        encoding="latin1",
    )
    if not username:
        raise ValueError("AP login name is empty")

    token, _offset = _read_nul_terminated_string(
        body,
        offset,
        label="credential",
        encoding="ascii",
    )
    token = token.lower()
    if not _AP_TOKEN_RE.fullmatch(token):
        raise ValueError("AP credential is not a 32-hex password token")
    return username, token


def authenticate_ap_verify_body(
    body: bytes,
    *,
    db_path: str | Path | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """Parse and verify one native AP login request against the account DB."""
    username, token = parse_ap_verify_credentials(body)
    account = verify_ap_credential(
        username,
        token,
        db_path=db_path,
        update_last_login=True,
    )
    return username, account


def build_ap_result_plaintext(
    seqno: int,
    uid: int = 10001,
    *,
    ticket: bytes = b"LOCAL_TICKET_001",
    error_code: int = 0,
    error_message: bytes = b"\x00",
) -> bytes:
    """Build AP_CMD_RESULT, including the nonzero status used for rejection."""
    message = bytes(error_message or b"\x00")
    if not message.endswith(b"\x00"):
        message += b"\x00"
    ticket = bytes(ticket or b"")
    if len(ticket) > 0xFFFF:
        raise ValueError("AP result ticket is too long")

    body = (
        (int(error_code) & 0xFFFFFFFF).to_bytes(4, "big")
        + (0).to_bytes(4, "big")
        + len(message).to_bytes(4, "big")
        + message
        + (int(uid) & 0xFFFFFFFF).to_bytes(4, "big")
        + (int(time.time()) & 0xFFFFFFFF).to_bytes(4, "big")
        + len(ticket).to_bytes(2, "big")
        + ticket
    )
    if len(body) > 0xFFFF:
        raise ValueError("AP result body is too long")

    return (
        len(body).to_bytes(2, "big")
        + (1).to_bytes(2, "big")
        + (int(seqno) & 0xFFFFFFFF).to_bytes(4, "big")
        + (4).to_bytes(2, "big")
        + body
    )
