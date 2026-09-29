# Easy Getting Started Guide

This guide is written for people who just want to get the **stable public v143b emulator** running without knowing the Assault Fire protocol first.

Local username/password registration is available through the development
website at `127.0.0.1` (localhost). First-time in-game nickname/profile
creation is a separate client flow and is still being validated.

## The short version

You will do the basic backend setup, then verify the client launch handoff:

```text
1. Clone the repo
2. Install the Python dependency
3. Generate a local RSA key pair
4. Verify/patch TCLS raw-PEM APClient.dat compatibility
5. Redirect the old Assault Fire PH hostnames to 127.0.0.1
6. Start the v143b server and require preflight PASS / launch gate UNLOCKED (a brief LOCKED state while listeners bind is normal)
7. On first use, register an account at the local page opened by the server; use the same username and password in the Assault Fire launcher
8. Launch client.exe / TCLS and log in until START is available
9. Choose ONE compatibility path (both are blocked if preflight did not pass):
   - normal launch: patch_tgame_datetime.py
   - suspended launch: patch_tcls_suspended_launch.py
10. Click START
11. Confirm TGame reaches ROLE and ZONE
```

The account page normally uses `http://127.0.0.1:8080/register`. If port 8080
is busy, use the actual `[WEB] Registration` URL printed in the server window.
It is available only on the same PC running the local emulator.

Before your first test, also read **[Vital Launch Requirements](LAUNCH_REQUIREMENTS.md)**. It explains the TCLS → TGame shared-memory handoff and the build-specific launch patch that is easy to miss.

For PvE, v143b manages the lazy DS lifecycle: room creation reserves capacity, the stock room's selected map/settings are carried into that reservation, match start arms the bridge, and the first valid DS UDP packet starts the v48 AFDEV loader.

---

## 1. Clone the repository

Open PowerShell:

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

No Git? You can also use GitHub's **Code → Download ZIP**, extract it, and open PowerShell inside the extracted folder.

---

## 2. Install Python and the dependency

Python **3.10 or newer** is supported.

Check that Python works:

```powershell
py --version
```

Create a small virtual environment:

```powershell
py -m venv .venv
```

Install the dependency:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

You can use `.venv\Scripts\python.exe` for every command in this guide if plain `python` points at a different Python installation.

---

## 3. Generate your local RSA key pair

This is the easiest method. **You do not need OpenSSL.**

The Assault Fire PH AUTH protocol used by this project expects a **1024-bit RSA key** for legacy client compatibility. The server receives a 128-byte RSA ciphertext and produces a 128-byte signature, so a different RSA size will not work with this protocol.

> RSA-1024 is obsolete for modern security. This helper uses it only because the legacy game protocol requires it. Do not reuse this key for websites, SSH, certificates, passwords, or anything security-sensitive.

### Easiest one-command setup

Replace the example path below with the folder that contains your client's existing `APClient.dat`.

Typical client layout:

```text
<YOUR ASSAULT FIRE FOLDER>
└── TCLS
    └── config
        └── APClient.dat
```

Example:

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

The helper will:

1. generate `server\PRIVATE.PEM`;
2. generate the matching public key as `generated\APClient.dat`;
3. back up your current client `APClient.dat` if one already exists;
4. copy the new matching public key into your client's `TCLS\config\APClient.dat`.

Expected output looks roughly like:

```text
[OK] Generated a matching Assault Fire PH local RSA-1024 key pair.

[PRIVATE - SERVER]
  ...\server\PRIVATE.PEM
  Keep this file private. Never commit or upload it.

[PUBLIC - CLIENT]
  ...\generated\APClient.dat

[BACKUP] ...\TCLS\config\APClient.dat
      -> ...\APClient.dat.backup_YYYYMMDD_HHMMSS

[OK] Installed matching public key:
  ...\TCLS\config\APClient.dat
```

### Important: PRIVATE.PEM and APClient.dat must match

Think of them as a pair:

```text
server\PRIVATE.PEM          <---- matching pair ---->   TCLS\config\APClient.dat
PRIVATE KEY                                            PUBLIC KEY
server keeps this                                     client uses this
NEVER upload it                                       safe to regenerate
```

If you generate a new `PRIVATE.PEM` but keep an old `APClient.dat`, AUTH will fail.

### Never upload PRIVATE.PEM

The repository's `.gitignore` blocks `PRIVATE.PEM`, `*.PEM`, and generated key files, but still check before every push:

```powershell
git status --short
```

You should **never** see `server\PRIVATE.PEM` staged for commit.

### If you only want to generate the files

Run:

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py
```

That creates:

```text
server\PRIVATE.PEM
generated\APClient.dat
```

Then copy `generated\APClient.dat` yourself to:

```text
<YOUR GAME FOLDER>\TCLS\config\APClient.dat
```

### Client compatibility note

The known working local setup uses `APClient.dat` as a raw PEM RSA-1024 public key. The original PH TCLS build required the already-known small local loader patch so it accepts that raw PEM file.

This repository does **not** distribute a modified `TCLS.dll`.

If VERSION works but AUTH fails immediately at the RSA step even though the two generated files match, check that your local TCLS setup is the version/configuration that reads the raw PEM `APClient.dat`.

---

## 4. Verify TCLS raw-PEM APClient.dat compatibility

Before launching the client, verify the exact `TCLS.dll` used by your Assault Fire PH installation:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

For the supported PH v1.0.0.24 setup, the diagnostic recognizes these verified states:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
  -> original/pre-patch TCLS; raw APClient.dat compatibility patch is required

3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
  -> verified patched TCLS; no APClient loader patch is needed
```

If the original `13EAD403...` build is detected, fully close `client.exe` / TCLS and run:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

The helper verifies the exact source hash and instruction bytes, creates `TCLS.dll.bak`, applies only the recovered compatibility edits, and verifies the final known-good hash. **Do not force this patch onto an unknown TCLS build.**

Before continuing, the diagnostic must show the supported TCLS class and both RSA checks passing:

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

Keep the same client root available to the server in this PowerShell session:

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
```

The server re-checks this exact client copy during startup. For PvE, a correctly configured `AF_GAME_DIR=...\Binaries\Win32` can also supply the client root.

This is the step to check when the launcher reports **`AP client initialization failed.`** even though `server\PRIVATE.PEM` and `TCLS\config\APClient.dat` are a matching generated pair.

---

## 5. Redirect the retired Assault Fire PH services to localhost

The local emulator needs the old PH service names to resolve to your own PC.

The three mappings are:

```text
127.0.0.1    tversion.levelupgames.ph
127.0.0.1    tauthproxy.levelupgames.ph
127.0.0.1    tdir.levelupgames.ph
```

### Easiest method

Open **PowerShell as Administrator**, go to the repository folder, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

The helper:

- backs up your current Windows hosts file;
- removes conflicting entries only for these three Assault Fire PH names;
- adds the localhost mappings;
- flushes the Windows DNS cache.

A plain copy of the mappings is also available at:

```text
config\hosts.txt
```

### Manual method

Open Notepad as Administrator and edit:

```text
$env:SystemRoot\System32\drivers\etc\hosts
```

Add the three lines, save, then run:

```powershell
ipconfig /flushdns
```

---

## 6. Start the stable v143b emulator

Run it from the **repository root**:

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

If PowerShell says `.\.venv\Scripts\python.exe` is not recognized, `cd` back to the repository root first. The `.venv` directory is there, not inside `server\`.

The server automatically looks for:

```text
server\PRIVATE.PEM
```

Before any listener opens, the startup preflight checks the client, RSA/APClient pair, and Windows hosts file. A successful start includes:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph   : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph : YES
[PREFLIGHT] hosts tdir.levelupgames.ph       : YES
[PREFLIGHT] game launch gate         : UNLOCKED
[PREFLIGHT] PASS - all required checks succeeded; supported game launch helpers are UNLOCKED.
[VERSION] Listening on port 9060
[AUTH] Listening on port 8000
[DIR] Listening on port 9010
...
[MAIN] All listeners running.
```

A healthy run can print `game launch gate : LOCKED` immediately after the client checks pass. That temporary state only means the server is still pre-binding its required listeners. Wait for the later `game launch gate : UNLOCKED` and `[MAIN] All listeners running.` before starting either launch helper.

If any preflight rule fails, v143b exits with code 2 and **does not start VERSION / AUTH / DIR / ROLE / ZONE**. It also records `game launch gate : LOCKED`. The supported launch helpers refuse to arm/patch/resume the game until a later server run passes every required check.

A common blocked state looks like:

```text
[PREFLIGHT] client root             : None
[PREFLIGHT] TCLS validated build    : NO
[PREFLIGHT] APClient exact bytes    : NO
[PREFLIGHT] same RSA key            : NO
[PREFLIGHT] game launch gate         : LOCKED
```

The complete preflight block is appended to:

```text
server\af_server_live.log
```

and its machine-readable gate state is stored in:

```text
runtime\preflight_status.json
```

The launch helper also requires the server process from that status to still be alive, the core TCP listeners to belong to that process, and the TCLS loaded by `client.exe` to match the TCLS path that passed preflight.

Fix the reported client, RSA, TCLS, or hosts problem, restart the server, and do not click START until the gate says **UNLOCKED**.

If your private key is stored somewhere else, you can point the server to it:

```powershell
$env:AF_PRIVATE_KEY = "<private-dir>\PRIVATE.PEM"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Optional log path:

```powershell
$env:AF_LOG_PATH = "<log-dir>\server.log"
```

Keep the server window open while testing.

---

## Before launching: legacy security-driver compatibility

The original Assault Fire PH client includes a legacy kernel-level security / anti-cheat component designed for an older Windows environment.

On modern Windows, this old component can cause startup failures, crashes, driver initialization errors, or other instability even when the local emulator is responding correctly.

For preservation testing, some users may need a local test environment where that obsolete security-driver path is not active or is otherwise avoided.

This repository does **not** provide instructions or tooling for defeating active anti-cheat/security systems.

Any operating-system, driver, boot-policy, virtualization, or security configuration changes a user independently chooses to make are at that user's own risk. The project maintainers/contributors are not responsible for system instability, data loss, security problems, driver failures, or other consequences caused by third-party tools, original game drivers, or user-performed system changes.

See [Issue #4](https://github.com/armangido/af-emulator/issues/4), [Vital Setup Notes](VITAL_SETUP_NOTES.md), and [DISCLAIMER.md](../DISCLAIMER.md).

---

## 7. Choose one client compatibility path

The validated PH client needs the TGame datetime compatibility fix. There are now **two ways** to apply it. Use only one for a given launch.

### Path A — normal TCLS launch

This helper first checks the server's persisted preflight gate. If preflight is missing, failed, stale, or the required backend listeners are not active under that server process, it exits with `GAME LAUNCH BLOCKED`.

If your TCLS already launches TGame reliably, start the standalone datetime patcher in a second PowerShell window:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

It waits for `TGame.exe`, verifies:

```text
TGame.exe + 0x010B9510
expected: 83 EC 24 53 8B 5C 24 2C
```

and applies the runtime-only datetime fix.

### Path B — debugger-free suspended TCLS launch

This is the recommended first-launch path. It will not arm TCLS unless server preflight is **UNLOCKED**, the server is still alive with its core listeners active, and the loaded TCLS is the exact copy that passed preflight.

If your setup needs the proven TCLS handoff timing, first launch `client.exe / TCLS`, log in, and stop at the normal **START** screen.

Close/detach x32dbg, then run:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

Wait for:

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

Then click START.

The combined helper will:

1. locate the loaded `TCLS.dll`;
2. verify `TCLS.dll+0x584E0 == 8B 55 18 52`;
3. temporarily change those bytes to `6A 04 90 90` so TGame is created suspended;
4. detect the new child `TGame.exe`;
5. restore the original TCLS bytes immediately;
6. apply `patch_tgame_datetime.py` to the suspended child;
7. resume the primary TGame thread;
8. print a final success summary.

This is runtime-only. It does not modify `TCLS.dll` or `TGame.exe` on disk.

If either TCLS or TGame has a signature mismatch, the helper stops instead of forcing the patch. If the datetime patch fails after child creation, TGame is intentionally left suspended rather than resumed into a known failure path.

For manual inspection, you can keep TGame suspended after both runtime patches:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py --leave-suspended
```

**Do not run the standalone datetime patcher at the same time as the combined helper.**

More details: [Vital Launch Requirements](LAUNCH_REQUIREMENTS.md) and [Issue #3](https://github.com/armangido/af-emulator/issues/3).

---

## 8. Verify the TCLS → TGame launch handoff

Do **not** treat the launcher and TGame as the same program. The normal retail path is:

```text
client.exe / TCLS
  -> GetLoginInfo / selected server
  -> CreateProcessW(TGame.exe -q <uin>)
  -> TCLS_SHAREDMEMEMORY<child PID>
  -> TGame.exe
  -> ROLE
  -> ZONE
```

On the validated PH TCLS build, these locations were recovered:

```text
TCLS.dll + 0x5C150   CLaunchUI::GetLoginInfo
TCLS.dll + 0x5C230   selected game-server lookup
TCLS.dll + 0x5C236   "Get Game Server Info fail!" check
TCLS.dll + 0x5E7B3   shared-memory CreateFileMappingW path
TCLS.dll + 0x584F4   CreateProcessW area
```

### Optional suspended-launch compatibility path

Some preservation setups need enough time to let TCLS finish the handoff and apply TGame compatibility work before TGame initializes.

At the normal launcher START stage, the validated build can temporarily use:

```text
TCLS.dll + 0x584E0
expected: 8B 55 18 52
patch   : 6A 04 90 90
```

That changes the creation flags to `CREATE_SUSPENDED`.

Rules:

- verify the expected four bytes first;
- patch process memory only;
- never distribute a modified `TCLS.dll`;
- restore `8B 55 18 52` immediately after the child TGame is observed;
- apply the TGame runtime compatibility patch while the child is suspended;
- resume TGame afterward;
- do not leave a debugger attached to TGame during normal protected initialization.

If your setup already launches TGame reliably, do **not** apply this just because it is documented.

Full details and failure diagnosis: **[LAUNCH_REQUIREMENTS.md](LAUNCH_REQUIREMENTS.md)**.

---

## Logging level (optional)

You can make the console quieter without losing development diagnostics.

Default:

```powershell
$env:AF_LOG_LEVEL = "INFO"
```

Available console levels are `DEBUG`, `INFO`, `WARNING`, and `ERROR`.

```text
DEBUG    prints everything
INFO     hides DEBUG
WARNING  shows WARNING + ERROR
ERROR    shows ERROR only
```

The important rule is that **the file log always keeps DEBUG and above regardless of the console level**. The default file is:

```text
server\af_server_live.log
```

So if a player uses `INFO` or `WARNING`, ask them for that file when diagnosing a bug; the hidden DEBUG records are still there.

Raw AUTH plaintext/ciphertext remains separately protected. Only enable it for a controlled local diagnostic with `AF_DEBUG_AUTH_HEX=1`.

---

## 9. Launch Assault Fire PH

Start the client using the same local client setup you normally use.

The hosts entries send VERSION/AUTH/DIR traffic to the emulator on your PC.

For the public **v143b** baseline, register the account credentials on the
local website first. For initial client testing, use an existing/local profile
path; first-game nickname/profile setup remains under validation.

Game AUTH now checks the username and password token against the `accounts`
table in the same SQLite file used by account registration. Set `AF_ACCOUNT_DB`
to that shared database path when the registration site and game server run
from separate checkouts. When an older account successfully logs in to the
website, the server derives and stores its native AP verifier so that the same
password works for game login.

### First things to check

| Check | Expected |
|---|---|
| VERSION reaches local server | ✅ |
| Login AUTH handshake reaches local server | ✅ |
| Registered account + correct password | ✅ |
| Registered account + incorrect password | Rejected |
| Unknown username | Rejected |
| Server list/DIR loads | ✅ |
| Existing registered profile reaches zone/login path | ✅ baseline target |
| Basic profile/property state | ✅ baseline target |
| Local username/password account registration | ✅ through the development website |
| First-game nickname/profile initialization | ❌ not yet supported as a stable public v143b flow |
| PvE dedicated-server/gameplay handoff + room-selected map | ✅ integrated on main |

See [STATUS.md](STATUS.md) for the detailed working/partial/broken matrix.

---

## 10. PvE map setup

You do **not** need the DS components just to test VERSION/AUTH/DIR/login. For PvE, the current v143b server manages them as part of the match lifecycle.

Current files:

```text
server\assaultfire_ds_spawner.py
tools\server_spawner\AFDevLoader_v48_spawner_multi_instance.py
tools\bridge\af_ds_udp_bridge_v9_multi_peer_latch.py
```

Set `AF_GAME_DIR` to the `Binaries\\Win32` directory of your Assault Fire PH installation (the drive letter/install location can be different), then start v143b:

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<full path to your Assault Fire PH Binaries\Win32 folder>"
$env:AF_DS_SPAWNER_ENABLED = "1"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

The lifecycle is lazy: A10A reserves capacity only and seeds the stock room's map/settings; A11E can update them before start; A3A0/A113 arms the bridge; the first valid DS UDP packet starts AFDEV; verified `SESSION_READY` releases the latched packet and the UE3 session goes live.

By default `AF_DS_USE_CLIENT_MAP=1`, so the selected stock-client `MapString` is used. Set it to `0` only if you intentionally want to force `AF_DS_DEFAULT_MAP`.

See **[Stable PvE bridge + server spawner guide](PVE_BRIDGE_AND_SPAWNER.md)** and **[PvE runtime and map selection](PVE_RUNTIME.md)**.

## 11. Super-simple troubleshooting

### Launcher says "AP client initialization failed."

First look at the emulator window. If you see VERSION traffic but **no `[AUTH] Connected ...`**, TCLS failed to initialize the AP client locally before it even reached the emulator's AUTH protocol.

Reinstall a matching generated APClient file into the exact client copy you launch:

~~~powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config" --force
~~~

Then verify:

~~~powershell
Get-Item "<game-root>\TCLS\config\APClient.dat" | Select-Object FullName,Length
Get-Content "<game-root>\TCLS\config\APClient.dat" -TotalCount 1
~~~

The repository-generated file should be **272 bytes** and start with:

~~~text
-----BEGIN PUBLIC KEY-----
~~~

Important: the known PH setup needs the client-side TCLS configuration that accepts this raw PEM form. If VERSION succeeds but AUTH is never opened, run **step 4** above and verify/patch the exact `TCLS.dll` used by the client. Repeatedly changing the server's AP response will not fix that stage.

Also, `TCLS.dll+0x584E0` is the **TGame suspended-launch patch**, not the APClient loader fix.

See **[Launcher / AP / TGame Error Reference](LAUNCHER_ERRORS.md#ap-client-initialization-failed)** for the full diagnosis.

### Server says it cannot load PRIVATE.PEM

Run the generator again:

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py
```

Then confirm this file exists:

```text
server\PRIVATE.PEM
```

### AUTH reaches the server but RSA decrypt fails

The most common thing to check first is that the client public key and server private key are from the **same generated pair**.

Regenerate/install both together:

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config" --force
```

Then restart both the server and client.

If it still fails immediately at RSA, verify your TCLS setup reads the raw PEM `APClient.dat`.

### The client tries the old internet host instead of localhost

Run Administrator PowerShell:

```powershell
ipconfig /flushdns
```

Then check:

```powershell
ping tversion.levelupgames.ph
```

It should resolve to:

```text
127.0.0.1
```

### Port already in use

The stable backend uses several local ports including:

```text
9060   VERSION
8000   AUTH
9010   DIR
65005  ROLE
65006  ZONE in the stable configuration
```

Close an older copy of the emulator before starting another one.

---

## 12. How to report a useful bug

Please include:

```text
Client version:
Server commit:
What I clicked/did:
What I expected:
What happened instead:

Relevant server log:
...

Packet command/opcode if known:
...

Does it reproduce after restarting both client and server?
Yes / No
```

Before posting logs publicly, remove:

- passwords;
- private keys;
- access tokens;
- personal account information;
- unrelated local filesystem details.

Never attach `PRIVATE.PEM`.

---

## 13. Easy ways to contribute

You do not have to know assembly.

Helpful contributions include:

- making the setup guide clearer;
- adding tests;
- documenting packet IDs;
- reproducing an issue and reporting exact steps;
- comparing sanitized packet captures;
- improving Python error messages;
- documenting which client UI action produces which request;
- helping verify partial lobby/social/clan/PvE behavior.

Please read [../CONTRIBUTING.md](../CONTRIBUTING.md) before submitting code.

Small changes with clear evidence are better than large guessed protocol implementations.
