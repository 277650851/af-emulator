# Stock item icon catalog audit

The item catalog stores an icon ID for each inventory item. This audit checks
those IDs against numeric Unreal package name-table entries and cross-checks
single-item commodity entries against the item's inventory icon ID.

For the supplied PH 1.0.0.24 files, the audit found 511 item rows and 471
unique nonzero icon IDs across `DefaultItemLibrary.ini`. Of 433 items with a
direct single-item commodity entry, 432 matched and one icon ID disagreed. The
CSV records the supplied catalogs before the proposed changes. The confirmed
test changes are:

| Item ID | Existing icon | Test icon | Evidence |
| ---: | ---: | ---: | --- |
| 100026 (default backpack) | 1000006 | 3000026 | `1000006` is absent from supplied `TG_Shop.upk`; `3000026` is present and is the No. 3 Backpack graphic. Both the item and its direct shop commodity entry are updated to keep them aligned. |
| 110004 (`SCAR_PHL`) | 3010004 | 3010006 | The direct commodity entry for item 110004 uses `3010006`, which exists in the shop package. |

The backpack test image visibly has a green “3”, because the available stock
graphic belongs to No. 3 Backpack. This is an explicit visual tradeoff while
the original generic icon asset is absent from the supplied package.

The original package scan found 11 referenced IDs not present in the uploaded
shop/UI package name tables. The proposed two item fixes use IDs that are
present, leaving these nine unresolved: `1000021`, `1000022`, `1000023`,
`1000041`, `1000042`, `3000294`, `3000501`, `3000601`, and `3000607`. Their
correct replacement images were not established, so the repair tool leaves
them alone. Some may live in other packages; absence from these three files is
not proof that the full client lacks a matching texture.

The CSV checks all 511 item rows for numeric icon-name presence in the three
provided packages and compares direct single-item commodity mappings. It is a
catalog consistency audit, not a visual review of every rendered icon. Rows
with icon ID zero and items without a direct commodity row are called out
separately.

## Test the change

Preview and generate the audit CSV:

```powershell
py -3.12 .\tools\patches\repair_item_icon_catalog.py --game-root "D:\AssaultFirePH - Copy"
```

After reviewing the preview, apply the two item corrections and the aligned
backpack commodity correction:

```powershell
py -3.12 .\tools\patches\repair_item_icon_catalog.py --game-root "D:\AssaultFirePH - Copy" --apply
```

The tool backs up both `DefaultItemLibrary.ini` and
`DefaultCommodityLibrary.ini` before writing, and restores the original files
if either write or verification fails. Restart `TGame` to reload the catalogs.
Python package `cryptography` is required for the game's AES-wrapped config
format.
