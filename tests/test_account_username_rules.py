from pathlib import Path
import tempfile

from server import account_db


with tempfile.TemporaryDirectory() as td:
    db = Path(td) / "accounts.sqlite3"
    old_iterations = account_db.PBKDF2_ITERATIONS
    account_db.PBKDF2_ITERATIONS = 1000
    try:
        for username in ("a", "ab"):
            try:
                account_db.create_account(username, "password1", db_path=db)
                raise AssertionError(f"too-short username accepted: {username!r}")
            except account_db.InvalidUsername:
                pass

        for username in ("abc", "lmao"):
            account_db.create_account(username, "password1", db_path=db)

        account = account_db.create_account("af001", "password1", db_path=db)
        assert account["uin"] == 10003
        assert account_db.verify_account("AF001", "password1", db_path=db) is not None
    finally:
        account_db.PBKDF2_ITERATIONS = old_iterations

print("ACCOUNT USERNAME RULE TEST: PASS")
