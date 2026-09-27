# Assault Fire Server Emulator

**언어:** [English](README.md) | **한국어** | [다른 언어](README-LANGUAGES.md)

비공식 **Assault Fire PH** 보존 및 서버 에뮬레이션 프로젝트입니다.

서비스가 종료된 PH 클라이언트를 로컬/격리 환경에서 다시 사용할 수 있도록 하여 보존, 상호운용성 연구, 테스트 및 추억을 위한 사용을 목표로 합니다.

> **지원 클라이언트: Assault Fire PH v1.0.0.24만 지원**
>
> 다른 버전은 binary, hash, packet layout, TCLS 동작 또는 offset이 다를 수 있으며 현재 지원하지 않습니다.

---

# 여기서 시작하세요

처음 사용하는 경우 아래 단계를 **순서대로** 진행하세요.

어떤 단계에서 **FAILED**가 나오면 그 문제를 먼저 해결한 뒤 다음 단계로 진행하세요.

## 필요한 것

- Windows 10/11
- Python 3.10+
- Git
- 본인이 보유한 Assault Fire PH **v1.0.0.24**
- 이 repository

원본 게임 client, map, package, executable 또는 proprietary game files는 포함되지 않습니다.

## 두 폴더를 구분하세요

### Repository folder

다음 구조가 있는 폴더에서 명령을 실행하세요:

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

PowerShell은 다음과 비슷해야 합니다:

```text
PS D:\Something\af-emulator>
```

**`server\` 폴더 안에서 명령을 실행하지 마세요.**

### Game root

`<game-root>`는 Assault Fire PH 설치 폴더를 의미합니다.

예:

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

**`<game-root>`를 그대로 입력하지 말고 실제 경로로 바꾸세요.**

---

## Logging level

Console을 조용하게 해도 development용 DEBUG log는 사라지지 않습니다.

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

사용 가능: `DEBUG`, `INFO`(기본값), `WARNING`, `ERROR`.

- `DEBUG` — console에 모든 로그 표시.
- `INFO` — DEBUG를 console에서 숨김.
- `WARNING` — WARNING과 ERROR만 표시.
- `ERROR` — ERROR만 표시.

**Console이 DEBUG가 아니어도 `server\af_server_live.log`에는 DEBUG 이상이 항상 저장됩니다.** Bug report와 development에 필요한 상세 기록은 유지됩니다.

Raw AUTH plaintext/ciphertext는 인증 정보를 포함할 수 있으므로 자동 저장하지 않습니다. Controlled local diagnostic에서만 `$env:AF_DEBUG_AUTH_HEX = "1"`을 사용하세요.

---

# Quick start

## 1. Emulator 받기

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

## 2. Python environment 생성

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Local RSA key pair 생성

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

생성되는 파일:

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **`server\PRIVATE.PEM`를 절대 upload/commit하지 마세요.**

## 4. TCLS와 APClient.dat 확인

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

다음이 보여야 합니다:

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

원본 TCLS SHA256이 다음이면:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

`client.exe`와 TCLS를 완전히 종료하고:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

검증된 patched SHA256:

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

patch 후 diagnostic을 다시 실행하세요.

## 5. 이전 PH service를 localhost로 redirect

**Administrator PowerShell**에서:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

필수 mapping:

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

## 6. Emulator 시작

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

정상 preflight:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

**FAILED**가 나오면 client를 계속 실행하지 말고 실패한 항목을 먼저 수정하세요.

---

# PvE

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

`AF_GAME_DIR`는 실제 `Binaries\Win32` 폴더를 가리켜야 합니다.

---

# Assault Fire PH 실행

둘 중 **하나만** 사용하세요.

## A — normal TCLS

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

## B — suspended TCLS handoff

TCLS에 로그인하고 **START** 화면에서 멈춘 다음:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

**같은 launch에서 두 helper를 모두 사용하지 마세요.**

## Mandatory preflight launch gate

Launch helper가 게임 실행을 계속 허용하기 전에 server preflight가 반드시 **PASS**해야 합니다:

```text
[PREFLIGHT] client root             : <실제 게임 폴더>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

Client checks가 PASS한 직후 server가 필수 listener를 모두 bind하는 동안 gate가 잠시 `LOCKED`로 표시되는 것은 **정상**입니다. 아직 launch하지 말고 이후의 `game launch gate : UNLOCKED`와 `[MAIN] All listeners running.`을 기다리세요.

`NO`, `client root : None` 또는 `game launch gate : LOCKED`가 하나라도 있으면 **START를 누르지 마세요**. Server listeners는 열리지 않고 지원되는 launch helper는 `GAME LAUNCH BLOCKED`와 함께 중지합니다.

전체 preflight report는 `server\af_server_live.log`에 기록되고 machine-readable gate state는 `runtime\preflight_status.json`에 저장됩니다. 문제를 수정하고 server를 다시 시작한 뒤 **UNLOCKED**일 때만 계속하세요.

---

# 자주 발생하는 문제

- `.venv python is not recognized` → repository root로 돌아가세요.
- `AP client initialization failed.` → diagnostic을 다시 실행하세요.
- AUTH까지 가지 않음 → TCLS/RSA/hosts가 모두 **YES**인지 확인하세요.
- `<game-root>`를 그대로 입력하지 마세요.
- **v1.0.0.24** 이외 버전은 지원하지 않습니다.

---

# 오래된 security driver 참고

원본 PH client에는 구형 Windows용 kernel security/anti-cheat component가 포함되어 있으며 modern Windows에서 emulator 연결 전에 실패할 수 있습니다.

이 프로젝트는 bypass, disable, kernel modification 또는 active security 우회 방법을 제공하지 않습니다.

[Vital Setup Notes](docs/VITAL_SETUP_NOTES.md)를 참고하세요.

# 문서

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Status](docs/STATUS.md)
- [PvE Runtime](docs/PVE_RUNTIME.md)
- [Launcher Errors](docs/LAUNCHER_ERRORS.md)
- [FAQ](docs/FAQ.md)

`PRIVATE.PEM`, password, account credentials 또는 proprietary game binaries를 upload하지 마세요.

# License

Original code와 documentation은 [MIT License](LICENSE)를 사용합니다.
