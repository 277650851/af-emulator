from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MallExpirationTests(unittest.TestCase):
    def test_catalog_timestamps_and_expiry_on_player_reload(self):
        with tempfile.TemporaryDirectory() as td:
            env = os.environ.copy()
            env.update(
                {
                    "AF_ACCOUNT_DB": str(Path(td) / "accounts.sqlite3"),
                    "AF_RUNTIME_MODE": "production",
                    "AF_DEV_WEB": "0",
                }
            )
            code = r"""
import struct
import assaultfire_server_v143b as s

# Catalog price index selects the matching Razorback duration.
assert s._v140_duration_hours(210006, 0) == 3
assert s._v140_duration_hours(210006, 3) == 168
assert s._v140_duration_hours(210001, 0) == -1
assert set(s.V140_SHOP_PRICES) <= set(s.V140_SHOP_AVAIL_HOURS)
for commodity_id, (_, prices) in s.V140_SHOP_PRICES.items():
    assert len(s.V140_SHOP_AVAIL_HOURS[commodity_id]) >= len(prices)

currency, _ = s._v140_price(210006, 3)
purchase = s._v140_plan_purchase(
    {
        "count": 1,
        "buy_type": 1,
        "consignne": 10001,
        "pay_type": s._v140_expected_pay_type(currency),
        "commodities": [{"commodity_id": 210006, "price_index": 3}],
    },
    self_uin=10001,
)
purchased = purchase["staged"][0]["props"][0]
assert purchased["validity"] == 168
assert purchased["expires_at"] - purchased["obtained_at"] == 168 * 3600

# PropInfo carries the selected duration and its acquisition time.
obtained_at = 1_700_000_000
wire = s._v109_pack_prop_info(
    1, 110004, avail_hours=168, obtain_time=obtained_at
)
assert struct.unpack_from(">Q", wire, 32)[0] == obtained_at
assert struct.unpack_from(">I", wire, 40)[0] == 168

# Simulate elapsed time in the persisted state, then reload the player as the
# server does at login. The expiring root and its owned bundle child disappear.
uin = 10001
s._v140_select_player(uin)
root_gid = s._v140_next_gid()
child_gid = s._v140_next_gid()
permanent_gid = s._v140_next_gid()
root = s._v140_make_prop(
    root_gid, 110004, duration_hours=3, obtained_at=1
)
child = s._v140_make_prop(
    child_gid, 100641, owner_gid=root_gid, duration_hours=-1, obtained_at=1
)
permanent = s._v140_make_prop(
    permanent_gid, 100642, duration_hours=-1, obtained_at=1
)
s.V111_INVENTORY.extend((root, child, permanent))
s.V140_MALL_STATE["current_role_gid"] = root_gid
s._v140_save_state("mall-expiry-test-setup")
stored = s.PLAYER_DB.load_player_state(uin)
stored_root = next(p for p in stored["inventory"] if p["gid"] == root_gid)
assert stored_root["obtained_at"] == 1
assert stored_root["expires_at"] == 1 + 3 * 3600

# A new process reloads this player's rows from SQLite before the expiry sweep.
s._V140_PLAYER_STATE._cache.pop(uin, None)
state = s._v140_select_player(uin)
remaining = {int(p["gid"]) for p in state["inventory"]}
assert root_gid not in remaining
assert child_gid not in remaining
assert permanent_gid in remaining
assert state["current_role_gid"] == s.V109_ROLE_GID

# The deletion is durable across another database reload.
reloaded = s.PLAYER_DB.load_player_state(uin)
remaining = {int(p["gid"]) for p in reloaded["inventory"]}
assert root_gid not in remaining
assert child_gid not in remaining
assert permanent_gid in remaining
"""
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=ROOT / "server",
                env=env,
                text=True,
                capture_output=True,
                timeout=30,
            )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"Mall expiry probe failed:\n{result.stdout}\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
