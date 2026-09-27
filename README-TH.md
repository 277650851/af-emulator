# Assault Fire Server Emulator

**ภาษา:** [English](README.md) | **ไทย** | [ภาษาอื่น](README-LANGUAGES.md)

โปรเจกต์ไม่เป็นทางการสำหรับการอนุรักษ์และจำลองเซิร์ฟเวอร์ **Assault Fire PH**

เป้าหมายคือทำให้ PH client ที่ยุติบริการแล้วสามารถใช้งานในสภาพแวดล้อม local/แยกออกมา เพื่อการอนุรักษ์ การวิจัย interoperability การทดสอบ และความคิดถึง

> **รองรับเฉพาะ Assault Fire PH v1.0.0.24**
>
> เวอร์ชันอื่นอาจมี binary, hash, packet layout, พฤติกรรม TCLS หรือ offset ต่างกัน และยังไม่รองรับ

---

# ⚠️ สำคัญ — ก่อนกด START

เพื่อให้การเปิดเกมครั้งแรกเสถียรที่สุด ให้ใช้ **suspended TCLS launch patcher** ก่อน

**อย่าเพิ่งกด START** ใน Assault Fire launcher

หลังจากทำ setup ด้านล่างเสร็จ เปิด emulator แล้ว login ผ่าน `client.exe` / TCLS และอยู่ที่หน้าจอ **START** ให้รันจาก repository root:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

รอจนเห็น:

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

**จากนั้นจึงกด START**

Helper จะทำ launch sequence ที่ถูกต้องอัตโนมัติ:

```text
TCLS creates TGame.exe suspended
        ↓
TCLS finishes the shared-memory handoff
        ↓
required TGame datetime compatibility patch is applied
        ↓
TGame.exe is resumed
```

วิธีนี้ช่วยหลีกเลี่ยง known legacy TGame startup crash ที่อาจเกิดขึ้นหากเกมเริ่มทำงานก่อน compatibility patch ถูกใช้งาน

> เมื่อใช้ `patch_tcls_suspended_launch.py` **อย่ารัน `patch_tgame_datetime.py` เพิ่มใน launch เดียวกัน** เพราะ suspended-launch helper ทำ datetime patch ให้อยู่แล้ว

ถ้า helper แจ้ง **TGame build/signature mismatch** ให้หยุดและอย่าฝืน patch ปัจจุบันรองรับ/ทดสอบเฉพาะ Assault Fire PH **v1.0.0.24**

## Logging level

คุณสามารถลดข้อความใน console ได้โดยไม่สูญเสีย development log

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

รองรับ `DEBUG`, `INFO` (ค่าเริ่มต้น), `WARNING`, `ERROR`.

- `DEBUG` — แสดงทุกอย่างใน console
- `INFO` — ซ่อน DEBUG จาก console
- `WARNING` — แสดงเฉพาะ WARNING และ ERROR
- `ERROR` — แสดงเฉพาะ ERROR

**แม้ console ไม่ได้เลือก DEBUG ไฟล์ `server\af_server_live.log` ก็ยังบันทึก DEBUG และ level ที่สูงกว่าทั้งหมดเสมอ** เพื่อใช้ในการพัฒนาและ bug report

Raw AUTH plaintext/ciphertext จะไม่ถูกบันทึกอัตโนมัติเพราะอาจมี credential/auth material ใช้เฉพาะ diagnostic local ที่ควบคุมได้: `$env:AF_DEBUG_AUTH_HEX = "1"`.

---

## Mandatory preflight launch gate

ก่อนที่ launch helper จะยอมให้เกมทำงานต่อ server preflight ต้อง **PASS** ก่อน:

```text
[PREFLIGHT] client root             : <โฟลเดอร์เกมจริง>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

หลังจาก client checks ผ่านแล้ว gate อาจแสดง `LOCKED` ชั่วคราวระหว่างที่ server bind listeners ที่จำเป็นทั้งหมด ซึ่งเป็น **ปกติ** อย่าเพิ่ง launch เกม ให้รอ `game launch gate : UNLOCKED` และ `[MAIN] All listeners running.`

ถ้ามี `NO`, `client root : None` หรือ `game launch gate : LOCKED` **อย่ากด START** Server จะไม่เปิด listeners และ supported launch helpers จะหยุดด้วย `GAME LAUNCH BLOCKED`.

Preflight report ทั้งหมดถูกเขียนไว้ที่ `server\af_server_live.log` และ machine-readable gate state อยู่ที่ `runtime\preflight_status.json`. แก้ปัญหา restart server และไปต่อเฉพาะเมื่อเห็น **UNLOCKED**.

---

# เริ่มที่นี่

ถ้าใช้โปรเจกต์นี้ครั้งแรก ให้ทำตามขั้นตอน **ตามลำดับ**

ถ้าขั้นตอนไหนขึ้น **FAILED** ให้แก้ก่อน แล้วค่อยไปต่อ

## สิ่งที่ต้องมี

- Windows 10/11
- Python 3.10+
- Git
- Assault Fire PH **v1.0.0.24** ของคุณเอง
- repository นี้

Repository นี้ไม่มี client เดิม, map, package, executable หรือไฟล์ proprietary ของเกม

## สองโฟลเดอร์สำคัญ

### Repository folder

รันคำสั่งจากโฟลเดอร์ที่มี:

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

PowerShell ควรคล้าย:

```text
PS D:\Something\af-emulator>
```

**อย่ารันคำสั่งจากข้างใน `server\`**

### Game root

`<game-root>` หมายถึงโฟลเดอร์ติดตั้ง Assault Fire PH ของคุณ

ตัวอย่าง:

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

**อย่าพิมพ์ `<game-root>` ตรงๆ ให้แทนด้วย path จริง**

---

# Quick start

## 1. ดาวน์โหลด emulator

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

## 2. สร้าง Python environment

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. สร้าง local RSA key pair

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

จะสร้าง:

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **ห้าม upload หรือ commit `server\PRIVATE.PEM`**

## 4. ตรวจ TCLS และ APClient.dat

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

ควรเห็น:

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

ถ้าพบ SHA256 เดิม:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

ปิด `client.exe` และ TCLS ให้หมด แล้วรัน:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

SHA256 ของ patched build ที่ยืนยันแล้ว:

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

แล้วรัน diagnostic อีกครั้ง

## 5. Redirect service PH เก่าไป localhost

เปิด **PowerShell as Administrator**:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

ต้องมี:

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

## 6. เริ่ม emulator

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Preflight ที่ถูกต้อง:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

ถ้า **FAILED** อย่าเปิด client ซ้ำๆ ให้แก้บรรทัดที่ผิดก่อน

---

# PvE

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

`AF_GAME_DIR` ต้องชี้ไปยัง `Binaries\Win32` จริง

---

# เปิด Assault Fire PH

เลือก **อย่างใดอย่างหนึ่ง**

## แบบ A — normal TCLS

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

## แบบ B — suspended TCLS handoff

ล็อกอิน TCLS และหยุดที่หน้า **START** แล้วรัน:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

**อย่าใช้ helper ทั้งสองใน launch เดียวกัน**

---

# ปัญหาที่พบบ่อย

- `.venv python is not recognized` → กลับไป repository root
- `AP client initialization failed.` → รัน diagnostic ใหม่
- ไปไม่ถึง AUTH → TCLS/RSA/hosts ต้องเป็น **YES**
- อย่าพิมพ์ `<game-root>` ตรงๆ
- เวอร์ชันอื่นนอกจาก **v1.0.0.24** ยังไม่รองรับ

---

# หมายเหตุ security driver เก่า

Client PH เดิมมี kernel security/anti-cheat รุ่นเก่าที่อาจมีปัญหาบน Windows สมัยใหม่ก่อนเชื่อมถึง emulator

โปรเจกต์นี้ไม่ให้คำแนะนำ bypass, disable, แก้ kernel หรือหลบระบบ security ที่กำลังใช้งาน

ดู [Vital Setup Notes](docs/VITAL_SETUP_NOTES.md)

# เอกสาร

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Status](docs/STATUS.md)
- [PvE Runtime](docs/PVE_RUNTIME.md)
- [Launcher Errors](docs/LAUNCHER_ERRORS.md)
- [FAQ](docs/FAQ.md)

ห้าม upload `PRIVATE.PEM`, password, account credentials หรือ binary proprietary ของเกม

# License

โค้ดและเอกสารต้นฉบับใช้ [MIT License](LICENSE)
