# PH clan system

The public server supports persistent clan operations for PH 1.0.0.24 in the
shared account SQLite database. The user confirmed creation, expansion,
badge setting and two-client invitations/acceptance in the October 5 session.
Promotion/demotion is implemented from the captured B020 request and recovered
schemas; live confirmation remains pending. Announcement handling, starter
badges and the full purchase catalog are integrated without claiming every
UI path has been verified.

## Protocol evidence

`clan_schema.json` records recovered field metadata from the supplied
`proto_c2zn.tdr`, SHA-256
`712d4eebfeeafe5c977530a59c7ce05d81cf203e2fb0cab1029653dca65758d2`.
Pointers resolve at `pointer + 0x114`; structure headers are `0xB8` bytes and
field descriptors are `0xB4` bytes. No game binary is redistributed.
`TGOnlineTeamRoom` scripts establish clan success as `0x9000`. Clan results
are 32-bit, unlike several other zone responses. Earlier guessed A601/A602
creation IDs are not aliases: PH creation uses B001/B002.

| Request | Response | Behavior |
|---|---|---|
| B00F | B010 | Verify clan name |
| B001 | B002 | Create clan, captain membership and starter badge |
| B005 | B006 | Search clan names |
| B009 | B00A + B00C | Detail and fresh roster on reopening |
| B00B | B00C | Roster, roles and current presence |
| B00D | B00E | Public clan details |
| B013 | B014 | Persist join application |
| B015 | B016 | Pending applications |
| B019 | B01A | Approve/reject applications |
| B02B | B02C + B01C to recipient | Invite an online player |
| B017 | B018 | Accept/decline invitation |
| B020 / B022 | B021 / B023 | Promote/demote selected member |
| B01E | B01F | Remove member with SafeCode |
| B024 | B08E | Leave clan |
| B025 | B026 | Expand capacity |
| B02D / B02F | B02E / B030 | Read/edit announcement |
| B080 | B081 | Edit introduction |
| B04A | B04B + B049 | Purchase badge components |
| B04E | B04F + B049 | Equip badge |
| B050 | B049 | Badge inventory |
| B051 | B052 | Public equipped badge lookup |
| B08A | B08B | Empty named subgroup list |

Roster packets contain Result:i32, IsAll:i8, TotalCount:i16, PackageFlag:u8
and nested ClanMembersInfo. FIRST/LAST flag bits are 1/2; packets contain up to
200 members. Presence bytes are offline=1 and online-idle=2. B009 sends the
roster because the captured reopen flow did not request B00B.

B02B is ManagerUin:u64, InvitedUin:u64. B02C puts InvitedUin:u64 before
ErrorCode:i32. B01C carries ClanID:u64, ClanName:TDR string, Invite_id:u64.
B017 contains IsAgree:u8, Uin:u64, ClanID:u64, Invite_id:u64. B018 contains
Result:i32, OfflineMsgId:u64, ClanID:u64, ClanName:TDR string. The client
recognizes 0x9000 for acceptance and 0x1025 for successful decline; offline
invite requests receive 0x1018.

Appointments use Uin:u64, ObjUin:u64, PlayerNewRole:u8; B021/B023 return
Result:i32 and ObjUin:u64. ClanRoleEnums values are captain=1, vicecaptain=2,
instructor=3, player=4, reserveplayer=5, honorarycaptain=6. The captain can
appoint any other member of their clan to a non-captain position, whether
online or offline. The stock panel's four honorary-captain limit is enforced.
Captain transfer is a separate operation and remains unimplemented.

## Badge fixes and policy

| Component | Catalog subtype | B049 ClanPropInfo.Type |
|---|---:|---:|
| Icon | 0 | 8 |
| Background | 2 | 9 |
| Frame | 1 | 10 |

ClanPropInfo.Type references CommodityDisplayTypeEnums, not the catalog's
sale subtype. Its pointer is 0x1959EF (file offset 0x195B03). Packed badge
fields use -1 for unequipped; legacy zero slots normalize to -1 without
changing real equipped components. The optional read-only
`tools/dev/verify_clan_badge_protocol.py` inspects these facts in the exact
fingerprinted metalib.

The numeric catalog contains 40 permanent PH commodities, currently priced
at 1 GP. Server catalog prices determine charges. The former ordinal cap of
seven components is disabled while clan progression is absent, allowing
commodity 200230 and other configured items. Unknown commodities, invalid
currency/options, insufficient funds and unowned/wrong-slot equipment remain
rejected. Rebuying an owned permanent component does not charge again.

New clans select the lowest permanent item ID in each catalog category and
grant/equip those three components atomically at no wallet cost. Current
defaults are icon 210001, frame 200001 and red background 220001. Retransmitted
creation preserves existing selections; existing clans are not backfilled.
Wallet debits, badge grants and moneyflow records share a transaction; the
mall cache reloads after purchase to avoid restoring stale funds.

## Persistence and limits

Membership, invitations, appointments, notices, capacity and badge ownership
persist in the account database. Clan schema version 2 migrations are additive.
A player belongs to at most one clan; names are unique after case folding.
Authenticated actor IDs and captain permissions are checked server-side.
SafeCode uses salted scrypt and credential-bearing payload logs are redacted.
Invitations and appointments validate recipient membership and clan scope
inside their transactions. Online members receive fresh profiles/menu state
after clan changes; offline players receive their stored membership at login.

Creation and expansion are free emulator policies because stock fees have
not been recovered. Initial capacity is 20, maximum expansion is 1,000.
Clan progression, captain transfer, dissolution, named groups, offline
notification delivery, clan chat, rewards, warehouses, timed badges and
renewal remain pending. Other operation permissions still require the captain;
full delegation by rank has not been implemented.

No new tests were added or run for this public integration, as requested.
Python syntax and JSON parsing were checked. Prior badge development had
local checks; they do not establish live acceptance of appointments.
