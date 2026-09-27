# Assault Fire Server Emulator

**Wika:** [English](README.md) | **Tagalog** | [Cebuano](README-CEB.md) | [简体中文](README-ZH-CN.md) | [Iba pang wika](README-LANGUAGES.md)

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![Engine](https://img.shields.io/badge/Engine-Unreal%20Engine%203-lightgrey)](#)
[![Status](https://img.shields.io/badge/status-preservation%20research-orange)](docs/STATUS.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Isang unofficial na **Assault Fire PH** preservation at server-emulation project.

Layunin nitong gawing magagamit muli ang retired PH client sa local/isolated environment para sa preservation, interoperability research, testing, at nostalgia.

> **Supported client:** Assault Fire PH **v1.0.0.24 lamang**.
>
> Posibleng iba ang binaries, hashes, packet layouts, TCLS behavior, o offsets ng ibang versions kaya hindi pa sila supported.

> Hindi affiliated, endorsed, o sponsored ng Tencent, Level Up! Games, o anumang original rights holder ang project na ito.

---

# ⚠️ IMPORTANTE — bago pindutin ang START

Para sa pinaka-reliable na first launch, gamitin muna ang **suspended TCLS launch patcher**.

**Huwag muna pindutin ang START** sa Assault Fire launcher.

Pagkatapos mong matapos ang setup sa ibaba, mapaandar ang emulator, makapag-login sa `client.exe` / TCLS, at makarating sa normal na **START** screen, pumunta sa repository root at patakbuhin:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

Hintayin munang lumabas:

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

**Saka lamang pindutin ang START.**

Awtomatikong ginagawa ng helper ang tamang launch sequence:

```text
TCLS creates TGame.exe suspended
        ↓
TCLS finishes the shared-memory handoff
        ↓
required TGame datetime compatibility patch is applied
        ↓
TGame.exe is resumed
```

Nakakaiwas ito sa kilalang legacy TGame startup crash kapag tumakbo ang game bago maging active ang compatibility patch.

> Kapag gumagamit ng `patch_tcls_suspended_launch.py`, **huwag ding patakbuhin ang `patch_tgame_datetime.py` sa parehong launch**. Kasama na iyon sa suspended-launch helper.

Kapag nag-report ang helper ng **TGame build/signature mismatch**, huminto at huwag pilitin ang patch. Assault Fire PH **v1.0.0.24 lamang** ang kasalukuyang supported/tested.

## Logging level

Puwedeng gawing tahimik ang console nang hindi nawawala ang development logs.

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

Mga level: `DEBUG`, `INFO` (default), `WARNING`, `ERROR`.

- `DEBUG` — ipinapakita lahat sa console.
- `INFO` — tinatago lang ang DEBUG sa console.
- `WARNING` — WARNING at ERROR lang.
- `ERROR` — ERROR lang.

**Kahit hindi DEBUG ang console, sine-save pa rin ng `server\af_server_live.log` ang DEBUG + lahat ng mas mataas na level.** Mahalaga ito para sa bug reports at development.

Ang raw AUTH plaintext/ciphertext ay hindi awtomatikong sine-save dahil maaaring may credential/auth material. Para lang sa controlled local diagnostic: `$env:AF_DEBUG_AUTH_HEX = "1"`.

---

## Mandatory preflight launch gate

Bago payagan ng launch helper ang game, kailangang **PASS** muna ang server preflight:

```text
[PREFLIGHT] client root             : <totoong game folder>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

**Normal lang** kung pansamantalang maging `LOCKED` ang gate pagkatapos pumasa ang client checks habang bina-bind ng server ang lahat ng required listeners. Huwag munang mag-launch. Hintayin ang susunod na `game launch gate : UNLOCKED` at `[MAIN] All listeners running.`

Kapag may `NO`, `client root : None`, o `game launch gate : LOCKED`, **huwag pindutin ang START**. Hindi magbubukas ang server listeners at mag-e-exit ang supported launch helpers na may `GAME LAUNCH BLOCKED`.

Nasa `server\af_server_live.log` ang buong preflight report at nasa `runtime\preflight_status.json` ang machine-readable gate state. I-restart ang server pagkatapos ayusin ang problema at magpatuloy lamang kapag **UNLOCKED**.

---

# Magsimula dito

Kung first time mong gamitin ang project, sundin ang mga step sa ibaba **sunod-sunod**.

Huwag laktawan ang failed step. Kapag may command na nagsabing **FAILED**, ayusin muna iyon bago magpatuloy.

## Mga kailangan

Kailangan mo ng:

- Windows 10/11
- Python 3.10+
- Git
- sarili mong Assault Fire PH **v1.0.0.24** installation
- repository na ito

Hindi kasama sa repository ang original game client, maps, packages, executables, o ibang proprietary game files.

## Importante: alamin ang dalawang folder

Dalawang magkaibang folder ang gagamitin mo.

### Repository folder

Ito ang folder na may README na ito at mga directory tulad ng:

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

Dito patakbuhin ang repository commands.

Dapat kahawig nito ang PowerShell prompt mo:

```text
PS D:\Something\af-emulator>
```

**Huwag patakbuhin ang commands habang nasa loob ng `server\`.**

### Game root

Ang Assault Fire PH folder mo ay tatawaging `<game-root>` sa documentation.

Halimbawa:

```text
D:\AssaultFirePH
├─ TCLS
│  ├─ Tenio
│  │  └─ TCLS.dll
│  └─ config
│     └─ APClient.dat
└─ Binaries
   └─ Win32
```

Sa halimbawang iyon:

```text
<game-root> = D:\AssaultFirePH
```

**Huwag literal na i-type ang `<game-root>`. Palitan ito ng totoong game folder mo.**

---

# Quick start

## 1. I-download ang emulator

Buksan ang PowerShell:

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

Kung ZIP ang dinownload mo, i-extract ito at mag-`cd` papunta sa extracted repository folder.

## 2. Gumawa ng Python environment

Habang nasa repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Checkpoint

Dapat mayroon na nito:

```text
.venv\Scripts\python.exe
```

Kapag sinabi ng PowerShell:

```text
.\.venv\Scripts\python.exe is not recognized
```

malamang nasa maling folder ka.

Patakbuhin:

```powershell
cd ..
```

hanggang bumalik ang prompt sa repository root, saka subukan ulit.

---

## 3. Gumawa ng local RSA key pair

Palitan ang `<game-root>` ng totoong Assault Fire PH folder mo:

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

Halimbawa:

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "D:\AssaultFirePH\TCLS\config"
```

Gagawa ito ng:

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **Huwag kailanman i-upload o i-commit ang `server\PRIVATE.PEM`.**

---

## 4. I-verify ang TCLS at APClient.dat

Patakbuhin:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

Halimbawa:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "D:\AssaultFirePH"
```

### Ito ang gusto mong makita

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

Kapag tama ang tatlo, magpatuloy sa step 5.

### Kapag original/pre-patch ang TCLS

Kapag ito ang SHA256:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

isara nang buo ang `client.exe` at TCLS, pagkatapos patakbuhin:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

Ang known patched SHA256 ay:

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

Gagawa ang patcher ng:

```text
TCLS.dll.bak
```

at tatanggihan nito ang unknown builds.

Pagkatapos mag-patch, **patakbuhin ulit ang diagnostic**.

Huwag magpatuloy hangga't hindi nakikita ang:

```text
exact byte match   : YES
same RSA key       : YES
```

---

## 5. I-redirect ang retired PH services sa localhost

Buksan ang **PowerShell as Administrator**.

Bumalik sa repository folder at patakbuhin:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

Kailangang ganito ang mappings:

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

Karaniwan hindi mo kailangang mano-manong i-edit ang hosts file; gamitin ang helper sa itaas.

---

## 6. Simulan ang emulator

Magbukas ng normal PowerShell window at bumalik sa repository root.

I-set ang game folder:

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
```

Halimbawa:

```powershell
$env:AF_CLIENT_ROOT = "D:\AssaultFirePH"
```

Pagkatapos simulan ang server:

```powershell
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

### Chine-check muna ng server ang setup bago magbukas ng ports

Hindi magpapatuloy ang startup kapag may required check na bumagsak.

Dapat may ganitong output:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

Pagkatapos lamang niyan dapat magsimula ang listeners:

```text
[VERSION] Listening on port 9060
[AUTH] Listening on port 8000
[DIR] Listening on port 9010
[ROLE] Listening on port 65005
[ZONE] Listening on port 65006
```

### Kapag FAILED ang preflight

**Huwag paulit-ulit na ilaunch ang client.**

Basahin ang failed line at ayusin ang mismong problemang iyon.

| Failure | Ayusin |
| --- | --- |
| `client root is unknown` | I-set ang `$env:AF_CLIENT_ROOT = "<game-root>"` |
| `TCLS validated build: NO` | Ulitin ang step 4 |
| `APClient exact bytes: NO` | Gumawa/install ulit ng matching `APClient.dat` |
| `same RSA key: NO` | Ulitin ang RSA generation sa step 3 |
| hosts check = `NO` | Ulitin ang step 5 gamit Administrator PowerShell |
| `PRIVATE.PEM not found` | Siguraduhing mayroon ang `server\PRIVATE.PEM` |

---

# PvE setup

Para sa PvE/dedicated-server gameplay, i-set muna ang variables na ito **bago** simulan ang v143b:

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Halimbawa:

```powershell
$env:AF_CLIENT_ROOT = "D:\AssaultFirePH"
$env:AF_GAME_DIR = "D:\AssaultFirePH\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Hindi importante ang drive letter. Ituro ang `AF_GAME_DIR` sa **totoong `Binaries\Win32` folder mo**.

Stable PvE flow:

```text
Create room
   ↓
reserve DS capacity
   ↓
press Start
   ↓
start the room bridge
   ↓
first valid gameplay packet
   ↓
start AFDEV
   ↓
SESSION_READY
   ↓
enter UE3 gameplay
```

Ang piniling stock PvE map/settings ay ipinapasa sa dedicated-server lifecycle.

Mas detalyado: **[PvE Runtime](docs/PVE_RUNTIME.md)**.

---

# 7. Ilunsad ang Assault Fire PH

Panatilihing bukas ang emulator PowerShell window.

Gumamit ng **isa lamang** sa dalawang compatibility path.

## Option A — normal TCLS launch

Patakbuhin:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

Pagkatapos mag-launch nang normal gamit ang `client.exe` / TCLS.

## Option B — suspended TCLS handoff

I-launch ang TCLS, mag-login, at huminto sa normal na **START** screen.

Pagkatapos patakbuhin:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

> Kasama na sa suspended-launch helper ang datetime compatibility patch.
>
> **Huwag gamitin ang dalawang launch helper sa iisang launch.**

---

# Mga karaniwang pagkakamali

### “.venv python is not recognized”

Malamang nasa maling folder ka.

Mali:

```text
PS D:\Something\af-emulator\server>
```

Tama:

```text
PS D:\Something\af-emulator>
```

### “AP client initialization failed.”

Ulitin ang step 4:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

Huwag manghula. Tingnan ang TCLS hash, exact-byte result, at RSA result.

### Nag-start ang server pero hindi umaabot sa AUTH ang client

Siguraduhing:

```text
TCLS validated build = YES
APClient exact bytes = YES
same RSA key = YES
hosts checks = YES
```

Pagkatapos tingnan ang **[Launcher Errors](docs/LAUNCHER_ERRORS.md)**.

### Literal kong kinopya ang `<game-root>`

Placeholder lang iyon.

Palitan ito ng totoong path, halimbawa:

```text
D:\AssaultFirePH
```

### Gumagamit ako ng ibang Assault Fire version

Ang repository ay kasalukuyang tested lamang sa:

```text
Assault Fire PH v1.0.0.24
```

Hindi inaasahang gagana agad ang ibang version nang walang karagdagang research.

---

# Legacy security-driver note

May legacy kernel-level security/anti-cheat component ang original PH client na ginawa para sa mas lumang Windows environment.

Sa modern Windows, maaari itong magdulot ng startup failures, crashes, o driver initialization problems **bago pa makausap ang emulator**.

Kapag bumabagsak ang client bago magkaroon ng normal VERSION/AUTH traffic, maaaring nasa client/OS compatibility layer ang problema at hindi sa emulator.

Hindi nagbibigay ang project na ito ng bypass, disabling, kernel-modification, o active security-circumvention instructions.

Tingnan ang **[Vital Setup Notes](docs/VITAL_SETUP_NOTES.md)**.

---

# Ano ang gumagana

Ang kasalukuyang public baseline ay **v143b**.

Kasama sa working/integrated areas:

- VERSION / AUTH / DIR / ROLE / ZONE local backend flow
- existing/local profile login path
- dynamic room support
- shared-room multiplayer work
- PvE dedicated-server allocation at lifecycle
- stock-selected PvE map/settings propagation
- lazy AFDEV startup
- v48 AFDEV loader
- v9 multi-peer UDP bridge
- zero-DSKey readiness path
- inventory/shop/profile preservation work

May ilang features na partial o under validation pa, kasama ang first-time nickname/account flow at ilang social/progression systems.

Tingnan ang **[Project Status](docs/STATUS.md)** para sa current matrix.

---

# Troubleshooting

| Problema | Basahin |
| --- | --- |
| First setup / hindi alam ang susunod | [Getting Started](docs/GETTING_STARTED.md) |
| AP/TCLS/TGame launcher error | [Launcher Errors](docs/LAUNCHER_ERRORS.md) |
| TCLS → TGame handoff problem | [Launch Requirements](docs/LAUNCH_REQUIREMENTS.md) |
| PvE / AFDEV / dedicated server | [PvE Runtime](docs/PVE_RUNTIME.md) |
| Legacy driver / modern Windows issue | [Vital Setup Notes](docs/VITAL_SETUP_NOTES.md) |
| Hindi sigurado kung implemented ang feature | [Project Status](docs/STATUS.md) |
| Common question | [FAQ](docs/FAQ.md) |

Kapag nagre-report ng bug, isama:

- exact error text
- anong step ka naroon
- command na pinatakbo mo
- huling relevant server/client log lines
- client version
- relevant hashes kung TCLS/TGame ang issue

**Huwag** i-upload ang `PRIVATE.PEM`, passwords, account credentials, o proprietary game binaries.

---

# Documentation

| Document | Para saan |
| --- | --- |
| [Getting Started](docs/GETTING_STARTED.md) | buong first-time setup |
| [Project Status](docs/STATUS.md) | implemented / partial / planned features |
| [PvE Runtime](docs/PVE_RUNTIME.md) | PvE at dedicated-server flow |
| [Launch Requirements](docs/LAUNCH_REQUIREMENTS.md) | TCLS → TGame requirements |
| [Launcher Errors](docs/LAUNCHER_ERRORS.md) | known AP/TCLS/TGame errors |
| [Architecture](docs/ARCHITECTURE.md) | ports, services, at data flow |
| [Research Findings](docs/RESEARCH_FINDINGS.md) | verified protocol/runtime findings |
| [FAQ](docs/FAQ.md) | common questions |
| [Contributing](CONTRIBUTING.md) | pag-contribute ng fixes at research |

---

# Project scope

Naglalaman ang repository ng original emulator code, documentation, at research tooling.

Huwag mag-commit ng:

- original game executables o DLLs
- maps, `.upk`, `.udk`, audio, textures, o ibang proprietary assets
- private keys
- passwords, tokens, cookies, o account credentials
- raw memory dumps na may proprietary o personal data
- files na wala kang karapatang i-redistribute

Dapat kunin ng users ang anumang required original game files nang independent at legal.

---

# License

Ang original code at documentation sa repository ay licensed sa ilalim ng [MIT License](LICENSE).

Hindi nagbibigay ang license ng rights sa Assault Fire, original client, executables, DLLs, maps, packages, artwork, audio, trademarks, o ibang third-party material.
