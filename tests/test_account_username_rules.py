from pathlib import Path
import tempfile

from server import account_db


with tempfile.TemporaryDirectory() as td:
    db = Path(td) / "accounts.sqlite3"

    for username in ("abc", "lmao"):
        try:
            account_db.create_account(username, "password1", db_path=db)
            raise AssertionError(f"short username accepted: {username!r}")
        except account_db.InvalidUsername:
            pass

    account = account_db.create_account("af001", "password1", db_path=db)
    assert account["uin"] == 10001
    assert account_db.verify_account("AF001", "password1", db_path=db) is not None

print("ACCOUNT USERNAME RULE TEST: PASS")
