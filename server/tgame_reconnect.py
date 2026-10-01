"""Parsing for the authenticated TGame cmd06 transport-resume request."""

from __future__ import annotations

import struct
from collections.abc import Callable


Mode3Decrypt = Callable[[bytes, bytes], bytes]


def parse_cmd06_resume(
    packet: bytes,
    key: bytes,
    decrypt_mode3: Mode3Decrypt,
) -> dict[str, int]:
    """Validate and decrypt the mode-3 cmd06 reconnect packet.

    cmd06 carries an encrypted auth header followed by an encrypted body. The
    header plaintext starts with the account UIN, and the body plaintext starts
    with the client's TPDU sequence. The returned UIN must be matched against
    a persisted session before the server accepts the reconnect.
    """
    packet = bytes(packet)
    key = bytes(key)
    if len(key) != 16:
        raise ValueError("TGame session key must be exactly 16 bytes")
    if len(packet) < 28 or packet[:3] != b"\x55\x0e\x06":
        raise ValueError("not a TGame cmd06 resume packet")

    head_len, body_len = struct.unpack(">II", packet[4:12])
    mode, service_id, _reserved, encrypted_head_len = struct.unpack(
        ">IIII", packet[12:28]
    )
    if mode != 3:
        raise ValueError(f"unsupported cmd06 encryption mode {mode}")
    if encrypted_head_len <= 0 or encrypted_head_len % 16:
        raise ValueError("invalid cmd06 encrypted header length")
    if head_len != 28 + encrypted_head_len:
        raise ValueError("cmd06 header length does not match encrypted header")
    if body_len <= 0 or body_len % 16:
        raise ValueError("invalid cmd06 encrypted body length")
    if head_len + body_len != len(packet):
        raise ValueError("cmd06 frame length does not match packet size")

    try:
        header_plain = decrypt_mode3(
            packet[28:head_len], key
        )
        body_plain = decrypt_mode3(
            packet[head_len:head_len + body_len], key
        )
    except Exception as exc:
        raise ValueError("cmd06 session-key verification failed") from exc

    if len(header_plain) < 4 or len(body_plain) < 4:
        raise ValueError("cmd06 plaintext is too short")
    uin = struct.unpack(">I", header_plain[:4])[0]
    sequence = struct.unpack(">I", body_plain[:4])[0]
    if uin <= 0:
        raise ValueError("cmd06 contains an invalid UIN")
    return {
        "mode": mode,
        "service_id": service_id,
        "uin": uin,
        "sequence": sequence,
    }
