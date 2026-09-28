#!/usr/bin/env python3
"""Read-only summary of the Assault Fire SQLite player-state tables."""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--db",
        default=str(Path(__file__).resolve().parents[1] / "server" / "assaultfire_accounts.sqlite3"),
    )
    args = ap.parse_args()
    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"Database does not exist: {db}")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        print(f"DB: {db}")
        for table in ("game_identities", "player_profiles", "player_wallets", "player_inventory"):
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if not exists:
                print(f"{table}: <missing>")
                continue
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {n}")

        print("\nPlayers:")
        rows = conn.execute(
            """
            SELECT gi.login_display, gi.uin, pp.nickname,
                   pw.ap, pw.gp, pw.mp,
                   pp.current_role_gid, pp.current_bag_gid,
                   (SELECT COUNT(*) FROM player_inventory pi WHERE pi.uin=gi.uin) AS inventory_count
            FROM game_identities gi
            LEFT JOIN player_profiles pp ON pp.uin=gi.uin
            LEFT JOIN player_wallets pw ON pw.uin=gi.uin
            ORDER BY gi.uin
            """
        ).fetchall()
        for r in rows:
            print(
                f"  login={r['login_display']!r} uin={r['uin']} "
                f"nickname={r['nickname']!r} "
                f"AP/GP/MP={r['ap']}/{r['gp']}/{r['mp']} "
                f"role={r['current_role_gid']} bag={r['current_bag_gid']} "
                f"inventory={r['inventory_count']}"
            )

        marker = conn.execute(
            "SELECT value FROM meta WHERE key='legacy_mall_state_imported'"
        ).fetchone()
        print("\nLegacy mall JSON import:", marker[0] if marker else "not imported")
    finally:
        conn.close()


if __name__ == "__main__":
    main()