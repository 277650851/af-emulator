# Assault Fire Server Emulator

**言語:** [English](README.md) | **日本語** | [その他の言語](README-LANGUAGES.md)

非公式の **Assault Fire PH** 保存・サーバーエミュレーションプロジェクトです。

サービス終了済みの PH クライアントをローカル/隔離環境で再利用し、保存、相互運用研究、テスト、懐古目的に使えるようにすることを目標としています。

> **対応クライアント: Assault Fire PH v1.0.0.24 のみ**
>
> 他のバージョンは binary、hash、packet layout、TCLS の挙動、offset が異なる可能性があり、現在は未対応です。

---

# ここから始めてください

初めて使う場合は、以下を**順番どおり**に実行してください。

途中で **FAILED** が出たら、その問題を直してから次へ進んでください。

## 必要なもの

- Windows 10/11
- Python 3.10+
- Git
- 自分で用意した Assault Fire PH **v1.0.0.24**
- この repository

元の game client、map、package、executable、その他 proprietary game files は含まれていません。

## 2つのフォルダを区別する

### Repository folder

次の構成があるフォルダからコマンドを実行します:

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

PowerShell は次のような状態にしてください:

```text
PS D:\Something\af-emulator>
```

**`server\` の中から実行しないでください。**

### Game root

`<game-root>` は Assault Fire PH のインストール先です。

例:

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

**`<game-root>` をそのまま入力せず、実際のパスに置き換えてください。**

---

## Logging level

Console を静かにしても development 用 DEBUG log は失われません。

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

利用可能: `DEBUG`, `INFO`（default）, `WARNING`, `ERROR`.

- `DEBUG` — console にすべて表示。
- `INFO` — DEBUG を console から隠す。
- `WARNING` — WARNING と ERROR のみ。
- `ERROR` — ERROR のみ。

**Console が DEBUG でなくても、`server\af_server_live.log` には DEBUG 以上が常に保存されます。** Bug report や development の詳細情報は失われません。

Raw AUTH plaintext/ciphertext は認証情報を含む可能性があるため自動保存しません。Controlled local diagnostic の場合のみ `$env:AF_DEBUG_AUTH_HEX = "1"` を使用してください。

---

# Quick start

## 1. Emulator を取得

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

## 2. Python environment を作成

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Local RSA key pair を生成

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

生成されるもの:

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **`server\PRIVATE.PEM` は絶対に upload/commit しないでください。**

## 4. TCLS と APClient.dat を確認

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

次の状態が必要です:

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

元の TCLS SHA256 が次の場合:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

`client.exe` と TCLS を完全に終了してから:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

確認済み patched SHA256:

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

patch 後に diagnostic を再実行してください。

## 5. 旧 PH service を localhost へ向ける

**Administrator PowerShell** で:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

必要な mapping:

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

## 6. Emulator を起動

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

正常な preflight:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

**FAILED** の場合は client を繰り返し起動せず、失敗した項目を修正してください。

---

# PvE

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

`AF_GAME_DIR` は実際の `Binaries\Win32` を指定してください。

---

# Assault Fire PH を起動

**どちらか1つだけ**使用してください。

## A — normal TCLS

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

## B — suspended TCLS handoff

TCLS で login して **START** 画面で止めてから:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

**同じ launch で両方を実行しないでください。**

## Mandatory preflight launch gate

Launch helper がゲームの続行を許可する前に、server preflight が **PASS** している必要があります:

```text
[PREFLIGHT] client root             : <実際のゲームフォルダ>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

Client checks が PASS した直後、server が必要な listener をすべて bind している間だけ gate が一時的に `LOCKED` になるのは**正常です**。まだ launch せず、後から表示される `game launch gate : UNLOCKED` と `[MAIN] All listeners running.` を待ってください。

`NO`、`client root : None`、または `game launch gate : LOCKED` がある場合は、**START を押さないでください**。Server listeners は開かず、対応 launch helper は `GAME LAUNCH BLOCKED` で停止します。

完全な preflight report は `server\af_server_live.log`、machine-readable gate state は `runtime\preflight_status.json` に保存されます。問題を修正して server を再起動し、**UNLOCKED** を確認してから続行してください。

---

# よくある問題

- `.venv python is not recognized` → repository root に戻る
- `AP client initialization failed.` → diagnostic をやり直す
- AUTH まで進まない → TCLS/RSA/hosts がすべて **YES** か確認
- `<game-root>` をそのまま入力しない
- **v1.0.0.24** 以外は未対応

---

# Legacy security driver について

元の PH client には古い Windows 向けの kernel security/anti-cheat component が含まれています。

Modern Windows では emulator に接続する前に失敗することがあります。

この project は bypass、disable、kernel modification、active security 回避手順を提供しません。

[ Vital Setup Notes ](docs/VITAL_SETUP_NOTES.md) を参照してください。

# Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Status](docs/STATUS.md)
- [PvE Runtime](docs/PVE_RUNTIME.md)
- [Launcher Errors](docs/LAUNCHER_ERRORS.md)
- [FAQ](docs/FAQ.md)

`PRIVATE.PEM`、password、account credentials、proprietary game binaries を upload しないでください。

# License

Original code/documentation は [MIT License](LICENSE) です。
