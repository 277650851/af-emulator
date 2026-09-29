from __future__ import annotations

import importlib.util
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYER_DB = ROOT / "server" / "player_db.py"
SERVER = ROOT / "server" / "assaultfire_server_v143b.py"

spec = importlib.util.spec_from_file_location("player_db_commit_test", PLAYER_DB)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def starter_state():
    return {
        "version": 1,
        "wallet": {"ap": 100000, "gp": 100000, "mp": 100000},
        "current_role_gid": 42953967927297,
        "current_bag_gid": 42953967927298,
        "next_gid": 42953967927310,
        "inventory": [],
    }


with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "accounts.sqlite3"
    db = mod.PlayerDatabase(path)
    u1 = db.resolve_identity("alpha01")
    u2 = db.resolve_identity("bravo01")
    db.ensure_player_state(u1, starter_state())
    db.ensure_player_state(u2, starter_state())

    assert db.claim_nickname(u1, "Nickname222") == "Nickname222"
    try:
        db.claim_nickname(u2, "NICKNAME222")
        raise AssertionError("duplicate nickname unexpectedly succeeded")
    except mod.PlayerDBError:
        pass

    db.claim_nickname(u1, "Éclair")
    assert db.nickname_available("éclair") is False
    try:
        db.claim_nickname(u2, "éclair")
        raise AssertionError("case-fold-equivalent Unicode nickname succeeded")
    except mod.PlayerDBError:
        pass
    assert db.claim_nickname(u1, "éCLAIR") == "éCLAIR"
    assert db.load_nickname(u1) == "éCLAIR"

    db.claim_nickname(u1, "AlphaOwn")
    db.claim_nickname(u2, "BravoOwn")
    u3 = db.resolve_identity("charlie01")
    db.ensure_player_state(u3, starter_state())
    db.claim_nickname(u3, "FirstSessionNick", require_unclaimed=True)
    try:
        db.claim_nickname(u3, "StaleSessionNick", require_unclaimed=True)
        raise AssertionError("stale first-login session overwrote nickname")
    except mod.PlayerDBError:
        pass
    assert db.claim_nickname(u3, "RenamedLater") == "RenamedLater"
    barrier = threading.Barrier(2)
    results = []
    lock = threading.Lock()

    def worker(uin):
        local = mod.PlayerDatabase(path)
        barrier.wait()
        try:
            local.claim_nickname(uin, "RaceNick")
            value = "ok"
        except mod.PlayerDBError:
            value = "rejected"
        with lock:
            results.append(value)

    a = threading.Thread(target=worker, args=(u1,))
    b = threading.Thread(target=worker, args=(u2,))
    a.start(); b.start(); a.join(); b.join()
    assert sorted(results) == ["ok", "rejected"], results

source = SERVER.read_text(encoding="utf-8")
assert "first_nickname_v26_deferred_login_groups" in source
assert "first_account_change_role_pending" in source
assert "idempotent-same-nickname" in source
assert "ZONE_FAIL_NICKNAME_EXIST = 0x0103" in source
a002 = source[source.index('elif app["cmd"] == TGAME_ZN_REQ_CREATEACCOUNT'):]
assert "eligible = bool(ok and (db_awaiting or same_nickname_retry))" in a002
claim = a002[a002.index("PLAYER_DB.claim_nickname("):]
assert "require_unclaimed=True" in claim[:400]
assert "unsupported first-account role pair" not in source
assert "result=0x0104 nickname-claim-failure" not in source

print("FIRST LOGIN NICKNAME TEST: PASS")
