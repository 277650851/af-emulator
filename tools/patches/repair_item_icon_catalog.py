#!/usr/bin/env python3
"""Audit and repair confirmed stock Assault Fire PH item-icon catalog errors.

The tool previews by default. It edits only the guarded fields listed in
ITEM_FIXES and COMMODITY_FIXES, verifies each replacement icon exists in a
scanned Unreal package, preserves both catalog encodings, and keeps timestamped
backups before applying changes.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import zlib

MAGIC = bytes.fromhex("f3f3f3f3")
AES_KEY = bytes.fromhex("5447414d451fe92c9a971a0cd1f610fb")

# Each item change is guarded by the exact stock value observed in the decoded
# DefaultItemLibrary.ini. The backpack graphic is an existing No. 3 bag image,
# so it removes the Img: placeholder but displays a green 3 on that card.
ITEM_FIXES = (
    {
        "item_id": 100026,
        "expected_icon_id": 1000006,
        "replacement_icon_id": 3000026,
        "reason": "1000006 is absent from TG_Shop; 3000026 is the existing No. 3 Backpack icon",
    },
    {
        "item_id": 110004,
        "expected_icon_id": 3010004,
        "replacement_icon_id": 3010006,
        "reason": "direct commodity entry for item 110004 uses icon 3010006",
    },
)

# Keep the backpack's shop/commodity card on the same available icon as its
# inventory entry. This is the one direct commodity row for item 100026.
COMMODITY_FIXES = (
    {
        "commodity_id": 1000026,
        "item_id": 100026,
        "expected_icon_id": 1000006,
        "replacement_icon_id": 3000026,
        "reason": "keep the default backpack shop icon aligned with its inventory icon",
    },
)

ITEM_ROW = re.compile(rb"RawItemDatas=\(([^\r\n]*)")
COMMODITY_ROW = re.compile(rb"RawCommodityDatas=\(([^\r\n]*)")
NUMERIC_NAME = re.compile(rb"(?=(\d{5,9})\x00)")


def decrypt_catalog(blob: bytes) -> bytes:
    if not blob.startswith(MAGIC):
        raise ValueError("Catalog is not in the expected encrypted PH format")
    if (len(blob) - 4) % 16:
        raise ValueError("Encrypted catalog has an invalid AES block length")
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    decryptor = Cipher(algorithms.AES(AES_KEY), modes.ECB()).decryptor()
    payload = decryptor.update(blob[4:]) + decryptor.finalize()
    if len(payload) < 4:
        raise ValueError("Encrypted catalog is truncated")
    expected = struct.unpack_from("<I", payload)[0]
    raw = zlib.decompress(payload[4:])
    if len(raw) != expected:
        raise ValueError("Decompressed catalog length does not match its header")
    return raw


def encrypt_catalog(raw: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    payload = struct.pack("<I", len(raw)) + zlib.compress(raw)
    payload += b"\0" * (-len(payload) % 16)
    encryptor = Cipher(algorithms.AES(AES_KEY), modes.ECB()).encryptor()
    return MAGIC + encryptor.update(payload) + encryptor.finalize()


def decode_text(raw: bytes) -> tuple[str, str, bytes]:
    if raw.startswith(b"\xff\xfe"):
        return raw[2:].decode("utf-16-le"), "utf-16-le", raw[:2]
    if raw.startswith(b"\xfe\xff"):
        return raw[2:].decode("utf-16-be"), "utf-16-be", raw[:2]
    try:
        raw.decode("utf-8")
        return raw.decode("utf-8"), "utf-8", b""
    except UnicodeDecodeError:
        return raw.decode("gbk"), "gbk", b""


def fields(row: bytes) -> dict[str, str]:
    result = {}
    for key, quoted, plain in re.findall(rb'\b(\w+)=(?:"([^"\r\n]*)"|([^,)]*))', row):
        value = quoted if quoted else plain.strip()
        result[key.decode("ascii")] = value.decode("gbk", errors="replace")
    return result


def parse_items(raw: bytes) -> list[dict[str, object]]:
    text, _, _ = decode_text(raw)
    rows = []
    encoded = text.encode("gbk", errors="replace")
    for match in ITEM_ROW.finditer(encoded):
        data = fields(match.group(1))
        if "nItemID" not in data or "nItemIconID" not in data:
            continue
        rows.append({
            "item_id": int(data["nItemID"]),
            "item_name": data.get("ItemName", ""),
            "icon_id": int(data["nItemIconID"]),
        })
    return rows


def parse_direct_commodities(raw: bytes) -> dict[int, set[int]]:
    text, _, _ = decode_text(raw)
    encoded = text.encode("gbk", errors="replace")
    direct: dict[int, set[int]] = {}
    for match in COMMODITY_ROW.finditer(encoded):
        row = match.group(1)
        data = fields(row)
        array = re.search(rb"\bnItemIDArray=\(([^)]*)\)", row)
        raw_items = re.findall(r"\d+", array.group(1).decode("ascii", errors="ignore")) if array else []
        if len(raw_items) != 1 or "IconID" not in data:
            continue
        direct.setdefault(int(raw_items[0]), set()).add(int(data["IconID"]))
    return direct


def package_numeric_names(path: Path) -> set[int]:
    """Read numeric FName entries from a UE package name table in one pass."""
    data = path.read_bytes()
    names: set[int] = set()
    for match in NUMERIC_NAME.finditer(data):
        token = match.group(1)
        start = match.start(1)
        # UE3 ANSI FString entries store (character count + NUL) immediately
        # before the text; this filters accidental numeric matches in bulk data.
        if start >= 4 and struct.unpack_from("<i", data, start - 4)[0] == len(token) + 1:
            names.add(int(token))
    return names


def get_catalog_paths(root: Path) -> tuple[Path, Path]:
    candidates = (
        root / "TGame" / "CookedPC" / "Config",
        root / "CookedPC" / "Config",
    )
    for directory in candidates:
        item = directory / "DefaultItemLibrary.ini"
        commodity = directory / "DefaultCommodityLibrary.ini"
        if item.is_file():
            return item, commodity
    raise FileNotFoundError("Could not find Config\\DefaultItemLibrary.ini; use --catalog")


def find_assets(root: Path, extra: list[Path]) -> list[Path]:
    candidates = [
        root / "TGame" / "CookedPC" / name
        for name in (
            "TG_Shop.upk", "TGUI_Texture.upk", "TGUI_Movies.upk",
            "TG_TeamBadge.upk", "TG_TeamBadgeAvatar.upk", "TG_RankIcons.upk",
            "UI_SpecialAwardIcon.upk", "Avatar_All.upk", "DefaultAvatar.upk",
        )
    ]
    candidates += [
        root / "CookedPC" / name
        for name in ("TG_Shop.upk", "TGUI_Texture.upk", "TGUI_Movies.upk")
    ]
    result = []
    for path in [*candidates, *extra]:
        path = path.resolve()
        if path.is_file() and path not in result:
            result.append(path)
    if not result:
        raise FileNotFoundError("No icon packages found; pass one or more --asset-package paths")
    return result


def apply_confirmed_fixes(raw: bytes, asset_ids: set[int]) -> tuple[bytes, list[str]]:
    text, encoding, bom = decode_text(raw)
    changes = []
    seen = set()
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if "RawItemDatas=(" not in line:
            continue
        match = ITEM_ROW.search(line.encode("gbk", errors="replace"))
        if not match:
            continue
        data = fields(match.group(1))
        if "nItemID" not in data:
            continue
        item_id = int(data["nItemID"])
        fix = next((entry for entry in ITEM_FIXES if entry["item_id"] == item_id), None)
        if fix is None:
            continue
        seen.add(item_id)
        icon_id = int(data["nItemIconID"])
        if icon_id == fix["replacement_icon_id"]:
            continue
        if icon_id != fix["expected_icon_id"]:
            raise ValueError(
                f"Item {item_id} has icon {icon_id}; expected {fix['expected_icon_id']} "
                f"or already-fixed {fix['replacement_icon_id']}. Refusing to overwrite local edits."
            )
        if fix["replacement_icon_id"] not in asset_ids:
            raise ValueError(
                f"Replacement icon {fix['replacement_icon_id']} was not found in scanned packages"
            )
        new_line = re.sub(
            rf"(\bnItemIconID=){fix['expected_icon_id']}\b",
            rf"\g<1>{fix['replacement_icon_id']}",
            line,
            count=1,
        )
        if new_line == line:
            raise ValueError(f"Could not replace icon field for item {item_id}")
        lines[index] = new_line
        changes.append(
            f"item {item_id}: {fix['expected_icon_id']} -> {fix['replacement_icon_id']}"
        )
    missing_rows = {fix["item_id"] for fix in ITEM_FIXES} - seen
    if missing_rows:
        raise ValueError(f"Expected catalog rows are missing for items: {sorted(missing_rows)}")
    if not changes:
        return raw, []
    return bom + "".join(lines).encode(encoding), changes


def apply_confirmed_commodity_fixes(raw: bytes, asset_ids: set[int]) -> tuple[bytes, list[str]]:
    """Patch only the confirmed direct commodity row, guarded by ID and item list."""
    text, encoding, bom = decode_text(raw)
    changes = []
    seen = set()
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if "RawCommodityDatas=(" not in line:
            continue
        match = COMMODITY_ROW.search(line.encode("gbk", errors="replace"))
        if not match:
            continue
        row = match.group(1)
        data = fields(row)
        if "nCommodityID" not in data:
            continue
        commodity_id = int(data["nCommodityID"])
        fix = next((entry for entry in COMMODITY_FIXES
                    if entry["commodity_id"] == commodity_id), None)
        if fix is None:
            continue
        seen.add(commodity_id)
        item_array = re.search(rb"\bnItemIDArray=\(([^)]*)\)", row)
        item_ids = [int(value) for value in re.findall(rb"\d+", item_array.group(1))] if item_array else []
        if item_ids != [fix["item_id"]]:
            raise ValueError(
                f"Commodity {commodity_id} targets item IDs {item_ids}; expected only "
                f"{fix['item_id']}. Refusing to overwrite local edits."
            )
        icon_id = int(data["IconID"])
        if icon_id == fix["replacement_icon_id"]:
            continue
        if icon_id != fix["expected_icon_id"]:
            raise ValueError(
                f"Commodity {commodity_id} has icon {icon_id}; expected "
                f"{fix['expected_icon_id']} or already-fixed {fix['replacement_icon_id']}. "
                "Refusing to overwrite local edits."
            )
        if fix["replacement_icon_id"] not in asset_ids:
            raise ValueError(
                f"Replacement icon {fix['replacement_icon_id']} was not found in scanned packages"
            )
        new_line = re.sub(
            rf"(\bIconID=){fix['expected_icon_id']}\b",
            rf"\g<1>{fix['replacement_icon_id']}",
            line,
            count=1,
        )
        if new_line == line:
            raise ValueError(f"Could not replace icon field for commodity {commodity_id}")
        lines[index] = new_line
        changes.append(
            f"commodity {commodity_id} (item {fix['item_id']}): "
            f"{fix['expected_icon_id']} -> {fix['replacement_icon_id']}"
        )
    missing_rows = {fix["commodity_id"] for fix in COMMODITY_FIXES} - seen
    if missing_rows:
        raise ValueError(f"Expected commodity rows are missing: {sorted(missing_rows)}")
    if not changes:
        return raw, []
    return bom + "".join(lines).encode(encoding), changes


def write_audit(
    item_raw: bytes,
    commodity_raw: bytes | None,
    package_names: dict[str, set[int]],
    report: Path,
) -> tuple[int, int, int]:
    items = parse_items(item_raw)
    direct = parse_direct_commodities(commodity_raw) if commodity_raw else {}
    all_asset_ids = set().union(*package_names.values()) if package_names else set()
    fields_out = [
        "item_id", "item_name", "icon_id", "icon_found_in_scanned_packages",
        "packages_with_icon", "direct_commodity_icon_ids", "direct_match_status",
        "confirmed_test_fix_icon_id",
    ]
    with report.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields_out)
        writer.writeheader()
        for item in items:
            item_id = int(item["item_id"])
            icon_id = int(item["icon_id"])
            direct_ids = sorted(direct.get(item_id, set()))
            if icon_id == 0:
                status = "ZERO_ICON_ID"
            elif not direct_ids:
                status = "NO_DIRECT_COMMODITY_CROSSCHECK"
            elif icon_id in direct_ids:
                status = "DIRECT_COMMODITY_MATCH"
            else:
                status = "DIRECT_COMMODITY_MISMATCH"
            writer.writerow({
                "item_id": item_id,
                "item_name": item["item_name"],
                "icon_id": icon_id,
                "icon_found_in_scanned_packages": "yes" if icon_id in all_asset_ids else "no",
                "packages_with_icon": ";".join(
                    Path(name).name for name, ids in package_names.items() if icon_id in ids
                ),
                "direct_commodity_icon_ids": ";".join(map(str, direct_ids)),
                "direct_match_status": status,
                "confirmed_test_fix_icon_id": next(
                    (fix["replacement_icon_id"] for fix in ITEM_FIXES if fix["item_id"] == item_id), ""
                ),
            })
    present_unique = len({int(item["icon_id"]) for item in items if item["icon_id"] and int(item["icon_id"]) in all_asset_ids})
    nonzero_unique = len({int(item["icon_id"]) for item in items if item["icon_id"]})
    missing_unique = nonzero_unique - present_unique
    mismatches = sum(1 for item in items if
        item["icon_id"] and direct.get(int(item["item_id"])) and
        int(item["icon_id"]) not in direct[int(item["item_id"])])
    return len(items), missing_unique, mismatches


def atomic_write(path: Path, data: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as out:
            temporary = out.name
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, help="Override DefaultItemLibrary.ini path")
    parser.add_argument("--commodities", type=Path, help="Override DefaultCommodityLibrary.ini path")
    parser.add_argument("--asset-package", type=Path, action="append", default=[],
                        help="Extra .upk to scan; may be repeated")
    parser.add_argument("--report", type=Path, default=Path("item_icon_audit.csv"))
    parser.add_argument("--audit-only", action="store_true", help="Write the audit without previewing fixes")
    parser.add_argument("--apply", action="store_true", help="Apply the confirmed item and commodity icon fixes")
    args = parser.parse_args()

    if args.catalog:
        catalog = args.catalog.resolve()
        inferred_commodity = catalog.with_name("DefaultCommodityLibrary.ini")
        commodity = (args.commodities.resolve() if args.commodities else
                     inferred_commodity if inferred_commodity.is_file() else None)
    else:
        catalog, commodity = get_catalog_paths(args.game_root.resolve())
        if args.commodities:
            commodity = args.commodities.resolve()
    if not catalog.is_file():
        raise FileNotFoundError(f"Item catalog not found: {catalog}")
    if commodity is not None and not commodity.is_file():
        commodity = None
    packages = find_assets(args.game_root.resolve(), args.asset_package)
    package_names = {str(path): package_numeric_names(path) for path in packages}
    asset_ids = set().union(*package_names.values())
    original_blob = catalog.read_bytes()
    raw = decrypt_catalog(original_blob)
    report = args.report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    total, missing_unique, mismatches = write_audit(
        raw,
        decrypt_catalog(commodity.read_bytes()) if commodity else None,
        package_names,
        report,
    )
    print(f"[ITEM-ICON] Catalog rows audited: {total}")
    print(f"[ITEM-ICON] Unique referenced icon IDs absent from scanned packages: {missing_unique}")
    print(f"[ITEM-ICON] Direct item-to-commodity icon disagreements: {mismatches}")
    print(f"[ITEM-ICON] Audit CSV: {report}")
    print(f"[ITEM-ICON] Packages scanned: {len(package_names)}")

    if args.audit_only:
        return 0
    changed_raw, changes = apply_confirmed_fixes(raw, asset_ids)
    commodity_raw = decrypt_catalog(commodity.read_bytes()) if commodity else None
    if commodity is None:
        raise FileNotFoundError(
            "DefaultCommodityLibrary.ini is required to apply coordinated icon fixes; "
            "pass --commodities"
        )
    changed_commodity_raw, commodity_changes = apply_confirmed_commodity_fixes(
        commodity_raw, asset_ids
    )
    all_changes = changes + commodity_changes
    if not all_changes:
        print("[ITEM-ICON] Confirmed fixes are already applied")
        return 0
    for change in all_changes:
        print(f"[ITEM-ICON] Planned: {change}")
    if not args.apply:
        print("[ITEM-ICON] Preview only; rerun with --apply to write both catalogs")
        return 0

    encoded = encrypt_catalog(changed_raw)
    encoded_commodity = encrypt_catalog(changed_commodity_raw)
    if decrypt_catalog(encoded) != changed_raw or decrypt_catalog(encoded_commodity) != changed_commodity_raw:
        raise ValueError("Encrypted catalog failed round-trip verification")
    original_item_blob = catalog.read_bytes()
    original_commodity_blob = commodity.read_bytes()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    item_backup = catalog.with_name(catalog.name + ".backup_" + timestamp)
    commodity_backup = commodity.with_name(commodity.name + ".backup_" + timestamp)
    shutil.copy2(catalog, item_backup)
    shutil.copy2(commodity, commodity_backup)
    try:
        atomic_write(catalog, encoded)
        atomic_write(commodity, encoded_commodity)
        if (decrypt_catalog(catalog.read_bytes()) != changed_raw or
                decrypt_catalog(commodity.read_bytes()) != changed_commodity_raw):
            raise ValueError("Written catalogs failed verification")
    except Exception:
        atomic_write(catalog, original_item_blob)
        atomic_write(commodity, original_commodity_blob)
        raise
    print(f"[ITEM-ICON] Applied and verified. Backups: {item_backup}, {commodity_backup}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ITEM-ICON] ERROR: {exc}")
        raise SystemExit(1)
