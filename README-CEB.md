# Assault Fire Server Emulator

**Pinulongan:** [English](README.md) | [Tagalog](README-TL.md) | **Cebuano** | [简体中文](README-ZH-CN.md) | [Ubang pinulongan](README-LANGUAGES.md)

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![Engine](https://img.shields.io/badge/Engine-Unreal%20Engine%203-lightgrey)](#)
[![Status](https://img.shields.io/badge/status-preservation%20research-orange)](docs/STATUS.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Usa kini ka unofficial nga **Assault Fire PH** preservation ug server-emulation project.

Ang tumong mao ang pagpabalik sa retired PH client aron magamit sa local/isolated environment para sa preservation, interoperability research, testing, ug nostalgia.

> **Supported client:** Assault Fire PH **v1.0.0.24 lamang**.
>
> Ang ubang versions mahimong lahi ang binaries, hashes, packet layouts, TCLS behavior, o offsets ug wala pa sila kasuportahi karon.

> Kini nga project dili affiliated, endorsed, o sponsored sa Tencent, Level Up! Games, o bisan unsang original rights holder.

---

# ⚠️ IMPORTANTE — sa dili pa nimo i-click ang START

Para sa pinakareliable nga first launch, gamita una ang **suspended TCLS launch patcher**.

**Ayaw sa pag-click og START** sa Assault Fire launcher.

Human nimo mahuman ang setup sa ubos, mapaandar ang emulator, maka-login sa `client.exe` / TCLS, ug makaabot sa normal nga **START** screen, adto sa repository root ug padagana:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

Hulata una nga mugawas:

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

**Human ra ana i-click ang START.**

Ang helper awtomatikong mohimo sa hustong launch sequence:

```text
TCLS creates TGame.exe suspended
        ↓
TCLS finishes the shared-memory handoff
        ↓
required TGame datetime compatibility patch is applied
        ↓
TGame.exe is resumed
```

Makatabang kini malikayan ang known legacy TGame startup crash kung modagan ang game sa dili pa ma-apply ang compatibility patch.

> Kung mogamit ka sa `patch_tcls_suspended_launch.py`, **ayaw usab pagdagan sa `patch_tgame_datetime.py` sa parehas nga launch**. Apil na ang datetime patch sa suspended-launch helper.

Kung mo-report og **TGame build/signature mismatch**, hunong ug ayaw pugsa ang patch. Assault Fire PH **v1.0.0.24 lamang** ang supported/tested karon.

## Logging level

Mahimo nimong pahilumon ang console nga dili mawala ang development logs.

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

Mga level: `DEBUG`, `INFO` (default), `WARNING`, `ERROR`.

- `DEBUG` — ipakita tanan sa console.
- `INFO` — itago lang ang DEBUG sa console.
- `WARNING` — WARNING ug ERROR lang.
- `ERROR` — ERROR lang.

**Bisan dili DEBUG ang console, ang `server\af_server_live.log` mag-save gihapon sa DEBUG ug tanang mas taas nga level.** Importante kini para sa bug reports ug development.

Ang raw AUTH plaintext/ciphertext dili automatic nga i-save tungod kay mahimong adunay credential/auth material. Para ra sa controlled local diagnostic: `$env:AF_DEBUG_AUTH_HEX = "1"`.

---

## Mandatory preflight launch gate

Sa dili pa tugotan sa launch helper ang game, kinahanglan **PASS** una ang server preflight:

```text
[PREFLIGHT] client root             : <tinuod nga game folder>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

**Normal ra** nga mahimong `LOCKED` kadiyot ang gate human mopasa ang client checks samtang gi-bind sa server ang tanan required listeners. Ayaw sa pag-launch. Hulata ang sunod nga `game launch gate : UNLOCKED` ug `[MAIN] All listeners running.`

Kung naay `NO`, `client root : None`, o `game launch gate : LOCKED`, **ayaw i-click ang START**. Dili mo-open ang server listeners ug ang supported launch helpers mohunong nga adunay `GAME LAUNCH BLOCKED`.

Ang full preflight report naa sa `server\af_server_live.log` ug ang machine-readable gate state naa sa `runtime\preflight_status.json`. Human ayuhon ang problema, i-restart ang server ug padayon lamang kung **UNLOCKED**.

---

# Sugdi dinhi

Kung first time nimo gamiton ang project, sundi ang mga step sa ubos **sunod-sunod**.

Ayaw laktawi ang failed step. Kung moingon ang command og **FAILED**, ayoha una ang problema bago mopadayon.

## Mga kinahanglan

Kinahanglan nimo:

- Windows 10/11
- Python 3.10+
- Git
- imong kaugalingong Assault Fire PH **v1.0.0.24** installation
- kini nga repository

Dili apil sa repository ang original game client, maps, packages, executables, o ubang proprietary game files.

## Importante: ilhi ang duha ka folders

Duha ka lain nga folder ang imong gamiton.

### Repository folder

Kini ang folder nga adunay README ug mga directory sama sa:

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

Dinhi padagana ang repository commands.

Ang imong PowerShell prompt dapat murag:

```text
PS D:\Something\af-emulator>
```

**Ayaw padagana ang commands sulod sa `server\`.**

### Game root

Ang imong Assault Fire PH folder tawgon og `<game-root>` sa documentation.

Pananglitan:

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

Sa maong pananglitan:

```text
<game-root> = D:\AssaultFirePH
```

**Ayaw literal nga i-type ang `<game-root>`. Ilisi kini sa tinuod nimong game folder.**

---

# Quick start

## 1. I-download ang emulator

Ablihi ang PowerShell:

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

Kung ZIP ang imong gi-download, i-extract kini ug mag-`cd` ngadto sa extracted repository folder.

## 2. Himoa ang Python environment

Samtang naa sa repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Checkpoint

Kinahanglan naa na kini nga file:

```text
.venv\Scripts\python.exe
```

Kung moingon ang PowerShell:

```text
.\.venv\Scripts\python.exe is not recognized
```

kasagaran naa ka sa sayop nga folder.

Padagana:

```powershell
cd ..
```

hangtod mobalik ang prompt sa repository root, unya sulayi pag-usab.

---

## 3. Himoa ang local RSA key pair

Ilisi ang `<game-root>` sa tinuod nimong Assault Fire PH folder:

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

Pananglitan:

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "D:\AssaultFirePH\TCLS\config"
```

Makahimo kini og:

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **Ayaw gyud i-upload o i-commit ang `server\PRIVATE.PEM`.**

---

## 4. I-verify ang TCLS ug APClient.dat

Padagana:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

Pananglitan:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "D:\AssaultFirePH"
```

### Mao ni ang gusto nimong makita

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

Kung sakto ang tulo, padayon sa step 5.

### Kung original/pre-patch ang TCLS

Kung makita ang SHA256:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

isira pag-ayo ang `client.exe` ug TCLS, dayon padagana:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

Ang known patched SHA256 mao ni:

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

Ang patcher mohimo og:

```text
TCLS.dll.bak
```

ug dili kini modawat og unknown builds.

Human mag-patch, **padagana pag-usab ang diagnostic**.

Ayaw padayon hangtod makita:

```text
exact byte match   : YES
same RSA key       : YES
```

---

## 5. I-redirect ang retired PH services ngadto sa localhost

Ablihi ang **PowerShell as Administrator**.

Balik sa repository folder ug padagana:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

Kinahanglan ingon niini ang mappings:

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

Kasagaran dili nimo kinahanglan mano-manong usbon ang hosts file; gamita ang helper sa taas.

---

## 6. Sugdi ang emulator

Ablihi ang normal nga PowerShell window ug balik sa repository root.

I-set ang game folder:

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
```

Pananglitan:

```powershell
$env:AF_CLIENT_ROOT = "D:\AssaultFirePH"
```

Dayon sugdi ang server:

```powershell
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

### I-check una sa server ang setup bago mag-open og ports

Dili mopadayon ang startup kung naay required check nga mapakyas.

Ang healthy startup dapat adunay:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

Human ra niini dapat magsugod ang listeners:

```text
[VERSION] Listening on port 9060
[AUTH] Listening on port 8000
[DIR] Listening on port 9010
[ROLE] Listening on port 65005
[ZONE] Listening on port 65006
```

### Kung FAILED ang preflight

**Ayaw sigeg launch sa client.**

Basaha ang failed line ug ayoha ang eksaktong problema.

| Failure | Unsay buhaton |
| --- | --- |
| `client root is unknown` | I-set ang `$env:AF_CLIENT_ROOT = "<game-root>"` |
| `TCLS validated build: NO` | Balika ang step 4 |
| `APClient exact bytes: NO` | I-regenerate/i-install pag-usab ang matching `APClient.dat` |
| `same RSA key: NO` | Balika ang RSA generation sa step 3 |
| hosts check = `NO` | Balika ang step 5 gamit Administrator PowerShell |
| `PRIVATE.PEM not found` | Siguroha nga naa ang `server\PRIVATE.PEM` |

---

# PvE setup

Para sa PvE/dedicated-server gameplay, i-set una kini nga variables **bago** sugdan ang v143b:

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Pananglitan:

```powershell
$env:AF_CLIENT_ROOT = "D:\AssaultFirePH"
$env:AF_GAME_DIR = "D:\AssaultFirePH\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Dili importante ang drive letter. Itudlo ang `AF_GAME_DIR` ngadto sa **tinuod nimong `Binaries\Win32` folder**.

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

Ang gipiling stock PvE map/settings ipadala ngadto sa dedicated-server lifecycle.

Mas detalye: **[PvE Runtime](docs/PVE_RUNTIME.md)**.

---

# 7. I-launch ang Assault Fire PH

Ayaw isira ang emulator PowerShell window.

Gamita ang **usa lamang** sa duha ka compatibility path.

## Option A — normal TCLS launch

Padagana:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

Dayon normal nga i-launch gamit ang `client.exe` / TCLS.

## Option B — suspended TCLS handoff

I-launch ang TCLS, mag-login, ug hunong sa normal nga **START** screen.

Dayon padagana:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

> Apil na sa suspended-launch helper ang datetime compatibility patch.
>
> **Ayaw gamita ang duha ka launch helper sa parehas nga launch.**

---

# Kasagarang mga sayop

### “.venv python is not recognized”

Kasagaran naa ka sa sayop nga folder.

Sayop:

```text
PS D:\Something\af-emulator\server>
```

Sakto:

```text
PS D:\Something\af-emulator>
```

### “AP client initialization failed.”

Balika ang step 4:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

Ayaw pagtag-an. Tan-awa ang TCLS hash, exact-byte result, ug RSA result.

### Nag-start ang server pero dili moabot sa AUTH ang client

Siguroha:

```text
TCLS validated build = YES
APClient exact bytes = YES
same RSA key = YES
hosts checks = YES
```

Dayon tan-awa ang **[Launcher Errors](docs/LAUNCHER_ERRORS.md)**.

### Literal nako gikopya ang `<game-root>`

Placeholder ra na.

Ilisi kini sa tinuod nga path, pananglitan:

```text
D:\AssaultFirePH
```

### Nag-usab ko og random DLLs/config files ug dili na mugana

Ibalik ang known-good client copy ug balika ang setup sugod sa step 3.

Ayaw gamita ang patches nga para sa laing TCLS/client hash.

### Lahi akong Assault Fire version

Ang repository karon tested lamang sa:

```text
Assault Fire PH v1.0.0.24
```

Dili gilauman nga mugana dayon ang ubang versions kung walay dugang research.

---

# Legacy security-driver note

Ang original PH client adunay legacy kernel-level security/anti-cheat component nga gihimo para sa mas karaang Windows environment.

Sa modern Windows, posible kini mahimong hinungdan sa startup failures, crashes, o driver initialization problems **bago pa makakonekta sa emulator**.

Kung mapakyas ang client bago makita ang normal VERSION/AUTH traffic, posible nga naa sa client/OS compatibility layer ang problema ug dili sa emulator.

Kini nga project dili mohatag og bypass, disabling, kernel-modification, o active security-circumvention instructions.

Tan-awa ang **[Vital Setup Notes](docs/VITAL_SETUP_NOTES.md)**.

---

# Unsay nagtrabaho

Ang current public baseline mao ang **v143b**.

Working/integrated areas:

- VERSION / AUTH / DIR / ROLE / ZONE local backend flow
- existing/local profile login path
- dynamic room support
- shared-room multiplayer work
- PvE dedicated-server allocation ug lifecycle
- stock-selected PvE map/settings propagation
- lazy AFDEV startup
- v48 AFDEV loader
- v9 multi-peer UDP bridge
- zero-DSKey readiness path
- inventory/shop/profile preservation work

Ang ubang features partial o under validation pa, lakip ang first-time nickname/account flow ug pipila ka social/progression systems.

Tan-awa ang **[Project Status](docs/STATUS.md)** para sa current matrix.

---

# Troubleshooting

| Problema | Basaha |
| --- | --- |
| First setup / wala kabalo unsay sunod | [Getting Started](docs/GETTING_STARTED.md) |
| AP/TCLS/TGame launcher error | [Launcher Errors](docs/LAUNCHER_ERRORS.md) |
| TCLS → TGame handoff problem | [Launch Requirements](docs/LAUNCH_REQUIREMENTS.md) |
| PvE / AFDEV / dedicated server | [PvE Runtime](docs/PVE_RUNTIME.md) |
| Legacy driver / modern Windows issue | [Vital Setup Notes](docs/VITAL_SETUP_NOTES.md) |
| Dili sigurado kung implemented ang feature | [Project Status](docs/STATUS.md) |
| Common question | [FAQ](docs/FAQ.md) |

Kung mag-report og bug, iapil:

- exact error text
- unsang step ka
- command nga imong gipadagan
- pinakabag-ong relevant server/client log lines
- client version
- relevant hashes kung TCLS/TGame ang issue

**Ayaw** i-upload ang `PRIVATE.PEM`, passwords, account credentials, o proprietary game binaries.

---

# Documentation

| Document | Para asa |
| --- | --- |
| [Getting Started](docs/GETTING_STARTED.md) | full first-time setup |
| [Project Status](docs/STATUS.md) | implemented / partial / planned features |
| [PvE Runtime](docs/PVE_RUNTIME.md) | PvE ug dedicated-server flow |
| [Launch Requirements](docs/LAUNCH_REQUIREMENTS.md) | TCLS → TGame requirements |
| [Launcher Errors](docs/LAUNCHER_ERRORS.md) | known AP/TCLS/TGame errors |
| [Architecture](docs/ARCHITECTURE.md) | ports, services, ug data flow |
| [Research Findings](docs/RESEARCH_FINDINGS.md) | verified protocol/runtime findings |
| [FAQ](docs/FAQ.md) | common questions |
| [Contributing](CONTRIBUTING.md) | pag-contribute og fixes ug research |

---

# Project scope

Ang repository adunay original emulator code, documentation, ug research tooling.

Ayaw pag-commit og:

- original game executables o DLLs
- maps, `.upk`, `.udk`, audio, textures, o ubang proprietary assets
- private keys
- passwords, tokens, cookies, o account credentials
- raw memory dumps nga adunay proprietary o personal data
- files nga wala kay katungod sa pag-redistribute

Kinahanglan kuhaon sa users ang required original game files sa independent ug legal nga paagi.

---

# License

Ang original code ug documentation niini nga repository licensed ubos sa [MIT License](LICENSE).

Ang license dili mohatag og rights sa Assault Fire, original client, executables, DLLs, maps, packages, artwork, audio, trademarks, o ubang third-party material.
