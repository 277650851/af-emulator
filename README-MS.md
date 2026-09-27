# Assault Fire Server Emulator

**Bahasa:** [English](README.md) | **Bahasa Melayu** | [Bahasa lain](README-LANGUAGES.md)

Projek tidak rasmi untuk pemeliharaan dan emulasi pelayan **Assault Fire PH**.

Matlamatnya ialah membolehkan klien PH yang telah dihentikan digunakan semula dalam persekitaran tempatan/terasing untuk pemeliharaan, penyelidikan interoperabiliti, ujian dan nostalgia.

> **Klien disokong: Assault Fire PH v1.0.0.24 sahaja.**
>
> Versi lain mungkin mempunyai binary, hash, packet layout, tingkah laku TCLS atau offset yang berbeza dan belum disokong.

---

# ⚠️ PENTING — sebelum menekan START

Untuk first launch yang paling stabil, gunakan **suspended TCLS launch patcher** terlebih dahulu.

**Jangan klik START** pada launcher Assault Fire lagi.

Selepas setup di bawah selesai, emulator sudah berjalan, anda sudah login melalui `client.exe` / TCLS dan sudah berada pada skrin **START**, jalankan dari root repository:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

Tunggu sehingga keluar:

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

**Selepas itu sahaja klik START.**

Helper akan melakukan urutan launch yang betul secara automatik:

```text
TCLS creates TGame.exe suspended
        ↓
TCLS finishes the shared-memory handoff
        ↓
required TGame datetime compatibility patch is applied
        ↓
TGame.exe is resumed
```

Ini membantu mengelakkan crash startup TGame lama jika game mula berjalan sebelum compatibility patch aktif.

> Apabila menggunakan `patch_tcls_suspended_launch.py`, **jangan jalankan `patch_tgame_datetime.py` untuk launch yang sama**. Datetime patch sudah termasuk dalam suspended-launch helper.

Jika helper melaporkan **TGame build/signature mismatch**, berhenti dan jangan paksa patch. Assault Fire PH **v1.0.0.24 sahaja** disokong/diuji sekarang.

## Logging level

Console boleh dibuat lebih senyap tanpa kehilangan log development.

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

Level tersedia: `DEBUG`, `INFO` (default), `WARNING`, `ERROR`.

- `DEBUG` — paparkan semuanya di console.
- `INFO` — sembunyikan DEBUG dari console.
- `WARNING` — WARNING dan ERROR sahaja.
- `ERROR` — ERROR sahaja.

**Walaupun console tidak memilih DEBUG, `server\af_server_live.log` tetap menyimpan DEBUG dan semua level yang lebih tinggi.** Ini penting untuk bug report dan development.

Raw AUTH plaintext/ciphertext tidak disimpan secara automatik kerana mungkin mengandungi credential/auth material. Hanya untuk diagnostic lokal terkawal: `$env:AF_DEBUG_AUTH_HEX = "1"`.

---

## Mandatory preflight launch gate

Sebelum helper membenarkan game diteruskan, server preflight mesti **PASS**:

```text
[PREFLIGHT] client root             : <folder game sebenar>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

Gate yang sementara menjadi `LOCKED` selepas client checks lulus adalah **normal** semasa server sedang bind semua listener yang diperlukan. Jangan launch lagi. Tunggu `game launch gate : UNLOCKED` dan `[MAIN] All listeners running.`

Jika ada `NO`, `client root : None`, atau `game launch gate : LOCKED`, **jangan klik START**. Listener server tidak dibuka dan helper launch yang disokong berhenti dengan `GAME LAUNCH BLOCKED`.

Laporan preflight penuh disimpan dalam `server\af_server_live.log`, dan status gate machine-readable berada dalam `runtime\preflight_status.json`. Baiki masalah, restart server, dan teruskan hanya apabila **UNLOCKED**.

---

# Mula di sini

Jika ini kali pertama anda menggunakan projek ini, ikut langkah di bawah **mengikut turutan**.

Jika satu langkah menunjukkan **FAILED**, baiki masalah itu dahulu sebelum meneruskan.

## Keperluan

- Windows 10/11
- Python 3.10+
- Git
- pemasangan Assault Fire PH **v1.0.0.24** anda sendiri
- repository ini

Repository ini tidak menyediakan klien permainan asal, map, package, executable atau aset proprietary lain.

## Dua folder penting

### Folder repository

Jalankan command dari folder yang mengandungi:

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

Prompt PowerShell sepatutnya kelihatan seperti:

```text
PS D:\Something\af-emulator>
```

**Jangan jalankan command dari dalam `server\`.**

### Game root

`<game-root>` bermaksud folder pemasangan Assault Fire PH anda.

Contoh:

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

**Jangan taip `<game-root>` secara literal. Gantikan dengan folder sebenar anda.**

---

# Quick start

## 1. Muat turun emulator

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

## 2. Cipta Python environment

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Jana pasangan RSA tempatan

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

Ia menghasilkan:

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **Jangan upload atau commit `server\PRIVATE.PEM`.**

## 4. Semak TCLS dan APClient.dat

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

Pastikan:

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

Jika SHA256 asal ini dikesan:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

tutup `client.exe` dan TCLS, kemudian:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

Hash patched yang disahkan:

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

Jalankan diagnostic sekali lagi sebelum meneruskan.

## 5. Redirect service PH lama ke localhost

Buka **PowerShell as Administrator**:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

Diperlukan:

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

## 6. Mulakan emulator

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Preflight yang sihat:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

Jika **FAILED**, jangan terus launch client. Baiki baris yang gagal dahulu.

---

# PvE

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Pastikan `AF_GAME_DIR` menunjuk ke `Binaries\Win32` sebenar.

---

# Launch Assault Fire PH

Pilih **satu** sahaja.

## Pilihan A — normal TCLS

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

## Pilihan B — suspended TCLS handoff

Berhenti pada skrin **START**, kemudian:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

**Jangan guna kedua-dua helper untuk launch yang sama.**

---

# Masalah biasa

- `.venv python is not recognized` → kembali ke root repository.
- `AP client initialization failed.` → ulang diagnostic TCLS/APClient.
- Tidak sampai AUTH → semua check TCLS/RSA/hosts mesti **YES**.
- Jangan taip `<game-root>` secara literal.
- Versi selain **v1.0.0.24** belum disokong.

---

# Nota security driver lama

Klien PH asal mempunyai komponen security/anti-cheat kernel lama yang mungkin gagal pada Windows moden sebelum emulator dihubungi.

Projek ini tidak menyediakan arahan bypass, disable, pengubahsuaian kernel atau pengelakan security aktif.

Lihat [Vital Setup Notes](docs/VITAL_SETUP_NOTES.md).

# Dokumentasi

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Status](docs/STATUS.md)
- [PvE Runtime](docs/PVE_RUNTIME.md)
- [Launcher Errors](docs/LAUNCHER_ERRORS.md)
- [FAQ](docs/FAQ.md)

Jangan upload `PRIVATE.PEM`, password, credentials atau binary game proprietary.

# License

Kod dan dokumentasi original menggunakan [MIT License](LICENSE).
