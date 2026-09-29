import hashlib
import sqlite3
import struct
import tempfile
import unittest
from pathlib import Path

from server import account_db
from server.assaultfire_ap_auth import (
    authenticate_ap_verify_body,
    build_ap_result_plaintext,
)


def make_verify_body(username: str, token: str) -> bytes:
    username_bytes = username.encode("latin1") + b"\x00"
    token_bytes = token.encode("ascii") + b"\x00"
    tail = b"\x00\x00\x00\x00\x01\x00\x00\x00"
    inner_size = 2 + 4 + len(username_bytes) + 4 + len(token_bytes) + len(tail)
    return (
        struct.pack(">H", inner_size)
        + struct.pack(">I", len(username_bytes))
        + username_bytes
        + struct.pack(">I", len(token_bytes))
        + token_bytes
        + tail
    )


class APAuthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "accounts.sqlite3"
        self.old_iterations = account_db.PBKDF2_ITERATIONS
        account_db.PBKDF2_ITERATIONS = 1000
        account_db.create_account("PlayerOne", "correct-horse-1", db_path=self.db)

    def tearDown(self):
        account_db.PBKDF2_ITERATIONS = self.old_iterations
        self.tmp.cleanup()

    def test_valid_native_password_token_authenticates_registered_account(self):
        token = hashlib.md5(b"correct-horse-1").hexdigest()

        username, account = authenticate_ap_verify_body(
            make_verify_body("PlayerOne", token), db_path=self.db
        )

        self.assertEqual(username, "PlayerOne")
        self.assertEqual(account["uin"], 10001)

    def test_wrong_password_token_is_rejected(self):
        token = hashlib.md5(b"wrong-password").hexdigest()

        username, account = authenticate_ap_verify_body(
            make_verify_body("PlayerOne", token), db_path=self.db
        )

        self.assertEqual(username, "PlayerOne")
        self.assertIsNone(account)

    def test_unknown_account_is_rejected(self):
        token = hashlib.md5(b"correct-horse-1").hexdigest()

        _username, account = authenticate_ap_verify_body(
            make_verify_body("UnknownUser", token), db_path=self.db
        )

        self.assertIsNone(account)

    def test_malformed_or_missing_credential_is_rejected(self):
        with self.assertRaises(ValueError):
            authenticate_ap_verify_body(b"\x00\x02\x00\x00", db_path=self.db)

        with self.assertRaises(ValueError):
            authenticate_ap_verify_body(
                make_verify_body("PlayerOne", "not-a-token"), db_path=self.db
            )

    def test_disabled_account_cannot_authenticate(self):
        conn = account_db.connect(self.db)
        try:
            conn.execute(
                "UPDATE accounts SET status='disabled' WHERE username_norm='playerone'"
            )
            conn.commit()
        finally:
            conn.close()

        token = hashlib.md5(b"correct-horse-1").hexdigest()
        _username, account = authenticate_ap_verify_body(
            make_verify_body("PlayerOne", token), db_path=self.db
        )

        self.assertIsNone(account)

    def test_failed_result_uses_nonzero_code_and_has_no_ticket(self):
        packet = build_ap_result_plaintext(
            9,
            uid=0,
            ticket=b"",
            error_code=1,
            error_message=b"Invalid account or password.",
        )

        self.assertEqual(int.from_bytes(packet[0:2], "big"), len(packet) - 10)
        self.assertEqual(int.from_bytes(packet[4:8], "big"), 9)
        self.assertEqual(int.from_bytes(packet[8:10], "big"), 4)
        body = packet[10:]
        self.assertEqual(int.from_bytes(body[0:4], "big"), 1)
        message_length = int.from_bytes(body[8:12], "big")
        self.assertTrue(body[12:12 + message_length].endswith(b"\x00"))
        offset = 12 + message_length
        self.assertEqual(int.from_bytes(body[offset:offset + 4], "big"), 0)
        ticket_length_offset = offset + 8
        self.assertEqual(int.from_bytes(body[ticket_length_offset:ticket_length_offset + 2], "big"), 0)

    def test_old_account_schema_is_migrated_without_authenticating_old_rows(self):
        legacy_db = Path(self.tmp.name) / "legacy.sqlite3"
        conn = sqlite3.connect(legacy_db)
        try:
            conn.execute(
                """
                CREATE TABLE accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uin INTEGER NOT NULL UNIQUE,
                    username TEXT NOT NULL,
                    username_norm TEXT NOT NULL UNIQUE,
                    password_hash BLOB NOT NULL,
                    password_salt BLOB NOT NULL,
                    password_iterations INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                )
                """
            )
            conn.execute(
                """INSERT INTO accounts(
                    uin,username,username_norm,password_hash,password_salt,
                    password_iterations,status,created_at
                ) VALUES(10001,'LegacyUser','legacyuser',X'00',X'00',1000,'active','now')"""
            )
            conn.commit()
        finally:
            conn.close()

        account_db.init_db(legacy_db)
        conn = account_db.connect(legacy_db)
        try:
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(accounts)")}
            self.assertTrue(
                {"ap_token_hash", "ap_token_salt", "ap_token_iterations"}.issubset(columns)
            )
        finally:
            conn.close()

        token = hashlib.md5(b"legacy-password").hexdigest()
        self.assertIsNone(
            account_db.verify_ap_credential("LegacyUser", token, db_path=legacy_db)
        )

    def test_successful_web_login_backfills_native_ap_verifier_for_old_rows(self):
        legacy_db = Path(self.tmp.name) / "legacy-valid.sqlite3"
        digest, salt, iterations = account_db._hash_password(
            "legacy-password",
            iterations=1000,
        )
        conn = sqlite3.connect(legacy_db)
        try:
            conn.execute(
                """
                CREATE TABLE accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uin INTEGER NOT NULL UNIQUE,
                    username TEXT NOT NULL,
                    username_norm TEXT NOT NULL UNIQUE,
                    password_hash BLOB NOT NULL,
                    password_salt BLOB NOT NULL,
                    password_iterations INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                )
                """
            )
            conn.execute(
                """INSERT INTO accounts(
                    uin,username,username_norm,password_hash,password_salt,
                    password_iterations,status,created_at
                ) VALUES(10001,'LegacyUser','legacyuser',?,?,?,'active','now')""",
                (digest, salt, iterations),
            )
            conn.commit()
        finally:
            conn.close()

        self.assertIsNotNone(
            account_db.verify_account(
                "LegacyUser",
                "legacy-password",
                db_path=legacy_db,
                update_last_login=True,
            )
        )
        token = hashlib.md5(b"legacy-password").hexdigest()
        self.assertIsNotNone(
            account_db.verify_ap_credential(
                "LegacyUser", token, db_path=legacy_db
            )
        )


if __name__ == "__main__":
    unittest.main()
