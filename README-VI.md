# Assault Fire Server Emulator

**Ngôn ngữ:** [English](README.md) | **Tiếng Việt** | [Ngôn ngữ khác](README-LANGUAGES.md)

Dự án không chính thức nhằm bảo tồn và mô phỏng máy chủ **Assault Fire PH**.

Mục tiêu là giúp client PH đã ngừng hoạt động có thể chạy lại trong môi trường local/cô lập để bảo tồn, nghiên cứu khả năng tương tác, thử nghiệm và hoài niệm.

> **Client được hỗ trợ: chỉ Assault Fire PH v1.0.0.24.**
>
> Các phiên bản khác có thể dùng binary, hash, packet layout, hành vi TCLS hoặc offset khác và hiện chưa được hỗ trợ.

---

# ⚠️ QUAN TRỌNG — trước khi bấm START

Để lần khởi động đầu tiên ổn định nhất, hãy dùng **suspended TCLS launch patcher** trước.

**Đừng bấm START** trong launcher Assault Fire lúc này.

Sau khi hoàn tất phần setup bên dưới, emulator đang chạy, bạn đã đăng nhập qua `client.exe` / TCLS và đang ở màn hình **START**, chạy từ root repository:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

Chờ tới khi hiện:

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

**Chỉ lúc đó mới bấm START.**

Helper sẽ tự động thực hiện đúng thứ tự:

```text
TCLS creates TGame.exe suspended
        ↓
TCLS finishes the shared-memory handoff
        ↓
required TGame datetime compatibility patch is applied
        ↓
TGame.exe is resumed
```

Điều này giúp tránh lỗi crash startup TGame cũ khi game bắt đầu chạy trước khi compatibility patch được áp dụng.

> Khi dùng `patch_tcls_suspended_launch.py`, **không chạy thêm `patch_tgame_datetime.py` trong cùng lần launch**. Suspended-launch helper đã áp dụng datetime patch.

Nếu helper báo **TGame build/signature mismatch**, hãy dừng lại và không ép patch. Hiện chỉ hỗ trợ/test Assault Fire PH **v1.0.0.24**.

## Logging level

Bạn có thể làm console gọn hơn mà vẫn giữ đầy đủ development log.

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

Các level: `DEBUG`, `INFO` (mặc định), `WARNING`, `ERROR`.

- `DEBUG` — hiện tất cả trên console.
- `INFO` — ẩn DEBUG trên console.
- `WARNING` — chỉ WARNING và ERROR.
- `ERROR` — chỉ ERROR.

**Ngay cả khi console không chọn DEBUG, `server\af_server_live.log` vẫn lưu DEBUG và mọi level cao hơn.** Điều này rất quan trọng cho bug report và development.

Raw AUTH plaintext/ciphertext không được tự động lưu vì có thể chứa credential/auth material. Chỉ dùng khi diagnostic local có kiểm soát: `$env:AF_DEBUG_AUTH_HEX = "1"`.

---

## Mandatory preflight launch gate

Trước khi helper cho phép game tiếp tục, server preflight phải **PASS**:

```text
[PREFLIGHT] client root             : <thư mục game thật>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

Việc gate tạm thời hiện `LOCKED` sau khi client checks đã PASS là **bình thường** trong lúc server bind toàn bộ listener bắt buộc. Đừng launch game lúc đó. Hãy chờ `game launch gate : UNLOCKED` và `[MAIN] All listeners running.`

Nếu có bất kỳ `NO`, `client root : None` hoặc `game launch gate : LOCKED`, **không bấm START**. Server sẽ không mở listener và các launch helper được hỗ trợ sẽ dừng với `GAME LAUNCH BLOCKED`.

Toàn bộ preflight report được ghi vào `server\af_server_live.log`; trạng thái gate machine-readable nằm trong `runtime\preflight_status.json`. Sửa lỗi, restart server và chỉ tiếp tục khi thấy **UNLOCKED**.

---

# Bắt đầu tại đây

Nếu đây là lần đầu bạn dùng dự án, hãy làm các bước dưới đây **đúng thứ tự**.

Nếu một bước báo **FAILED**, hãy sửa lỗi đó trước rồi mới tiếp tục.

## Yêu cầu

- Windows 10/11
- Python 3.10+
- Git
- bản Assault Fire PH **v1.0.0.24** của riêng bạn
- repository này

Repository không chứa client gốc, map, package, executable hoặc tài nguyên game proprietary.

## Hai thư mục quan trọng

### Thư mục repository

Chạy lệnh từ thư mục có:

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

PowerShell nên giống:

```text
PS D:\Something\af-emulator>
```

**Không chạy lệnh bên trong `server\`.**

### Game root

`<game-root>` là thư mục cài Assault Fire PH của bạn.

Ví dụ:

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

**Đừng gõ nguyên văn `<game-root>`. Hãy thay bằng đường dẫn game thật.**

---

# Quick start

## 1. Tải emulator

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

## 2. Tạo môi trường Python

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Tạo cặp RSA local

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

Tạo ra:

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **Không bao giờ upload hoặc commit `server\PRIVATE.PEM`.**

## 4. Kiểm tra TCLS và APClient.dat

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

Bạn cần thấy:

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

Nếu phát hiện SHA256 gốc:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

hãy đóng hoàn toàn `client.exe` và TCLS rồi chạy:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

SHA256 patched đã xác minh:

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

Sau đó chạy diagnostic lại.

## 5. Redirect dịch vụ PH cũ về localhost

Mở **PowerShell as Administrator**:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

Phải có:

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

## 6. Khởi động emulator

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Preflight đúng sẽ có:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

Nếu báo **FAILED**, đừng tiếp tục mở client. Hãy sửa đúng dòng lỗi trước.

---

# PvE

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

`AF_GAME_DIR` phải trỏ tới thư mục `Binaries\Win32` thật của bạn.

---

# Chạy Assault Fire PH

Chỉ chọn **một** cách.

## Cách A — normal TCLS

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

## Cách B — suspended TCLS handoff

Đăng nhập TCLS và dừng ở màn hình **START**, sau đó:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

**Không dùng cả hai helper cho cùng một lần chạy.**

---

# Lỗi thường gặp

- `.venv python is not recognized` → quay về root repository.
- `AP client initialization failed.` → chạy lại diagnostic.
- Không tới AUTH → TCLS/RSA/hosts đều phải **YES**.
- Không gõ nguyên văn `<game-root>`.
- Phiên bản khác **v1.0.0.24** chưa được hỗ trợ.

---

# Ghi chú security driver cũ

Client PH gốc có thành phần kernel security/anti-cheat cũ có thể lỗi trên Windows hiện đại trước khi emulator được liên hệ.

Dự án không cung cấp hướng dẫn bypass, disable, sửa kernel hoặc né hệ thống security đang hoạt động.

Xem [Vital Setup Notes](docs/VITAL_SETUP_NOTES.md).

# Tài liệu

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Status](docs/STATUS.md)
- [PvE Runtime](docs/PVE_RUNTIME.md)
- [Launcher Errors](docs/LAUNCHER_ERRORS.md)
- [FAQ](docs/FAQ.md)

Không upload `PRIVATE.PEM`, mật khẩu, thông tin tài khoản hoặc binary game proprietary.

# License

Code và tài liệu gốc dùng [MIT License](LICENSE).
