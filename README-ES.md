# Assault Fire Server Emulator

**Idioma:** [English](README.md) | **Español** | [Otros idiomas](README-LANGUAGES.md)

Proyecto no oficial de preservación y emulación de servidor para **Assault Fire PH**.

El objetivo es volver a utilizar el cliente PH retirado dentro de un entorno local/aislado para preservación, investigación de interoperabilidad, pruebas y nostalgia.

> **Cliente compatible: solo Assault Fire PH v1.0.0.24.**
>
> Otras versiones pueden usar binarios, hashes, packet layouts, comportamiento TCLS u offsets diferentes y no están soportadas actualmente.

---

# ⚠️ IMPORTANTE — antes de pulsar START

Para el primer inicio más fiable, usa primero el **suspended TCLS launch patcher**.

**No pulses START** todavía en el launcher de Assault Fire.

Después de completar la configuración de abajo, iniciar el emulator, iniciar sesión mediante `client.exe` / TCLS y llegar a la pantalla normal de **START**, ejecuta desde la raíz del repository:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

Espera hasta ver:

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

**Solo entonces pulsa START.**

El helper realiza automáticamente la secuencia correcta:

```text
TCLS creates TGame.exe suspended
        ↓
TCLS finishes the shared-memory handoff
        ↓
required TGame datetime compatibility patch is applied
        ↓
TGame.exe is resumed
```

Esto ayuda a evitar un crash conocido del TGame antiguo cuando el juego empieza a ejecutarse antes de que el compatibility patch esté activo.

> Si usas `patch_tcls_suspended_launch.py`, **no ejecutes también `patch_tgame_datetime.py` en el mismo launch**. El suspended-launch helper ya aplica el datetime patch.

Si aparece **TGame build/signature mismatch**, detente y no fuerces el patch. Actualmente solo se soporta/prueba Assault Fire PH **v1.0.0.24**.

## Logging level

Puedes hacer el console más silencioso sin perder los logs de desarrollo.

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

Niveles: `DEBUG`, `INFO` (por defecto), `WARNING`, `ERROR`.

- `DEBUG` — muestra todo en el console.
- `INFO` — oculta DEBUG del console.
- `WARNING` — solo WARNING y ERROR.
- `ERROR` — solo ERROR.

**Aunque el console no use DEBUG, `server\af_server_live.log` siempre guarda DEBUG y todos los niveles superiores.** Así se conserva la información necesaria para bugs y desarrollo.

Raw AUTH plaintext/ciphertext no se guarda automáticamente porque puede contener material de autenticación. Úsalo solo en un diagnóstico local controlado con `$env:AF_DEBUG_AUTH_HEX = "1"`.

---

## Mandatory preflight launch gate

Antes de que el helper permita continuar con el juego, el preflight del servidor debe estar en **PASS**:

```text
[PREFLIGHT] client root             : <carpeta real del juego>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

Es **normal** que el gate aparezca temporalmente como `LOCKED` después de pasar los client checks mientras el servidor hace bind de todos los listeners requeridos. No lances todavía. Espera `game launch gate : UNLOCKED` y `[MAIN] All listeners running.`

Si aparece cualquier `NO`, `client root : None` o `game launch gate : LOCKED`, **no pulses START**. Los listeners del servidor no se abren y los launch helpers soportados se detienen con `GAME LAUNCH BLOCKED`.

El preflight completo se guarda en `server\af_server_live.log` y el estado machine-readable del gate en `runtime\preflight_status.json`. Corrige el problema, reinicia el servidor y continúa solo cuando diga **UNLOCKED**.

---

# Empieza aquí

Si es tu primera vez usando el proyecto, sigue los pasos **en orden**.

Si un paso muestra **FAILED**, corrige ese problema antes de continuar.

## Necesitas

- Windows 10/11
- Python 3.10+
- Git
- tu propia instalación de Assault Fire PH **v1.0.0.24**
- este repository

Este repository no incluye el cliente original, mapas, packages, ejecutables ni otros archivos proprietary del juego.

## Distingue las dos carpetas

### Carpeta del repository

Ejecuta los comandos desde la carpeta que contiene:

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

PowerShell debería verse parecido a:

```text
PS D:\Something\af-emulator>
```

**No ejecutes los comandos desde dentro de `server\`.**

### Game root

`<game-root>` significa la carpeta donde está instalado Assault Fire PH.

Ejemplo:

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

**No escribas literalmente `<game-root>`. Sustitúyelo por tu ruta real.**

---

# Inicio rápido

## 1. Descargar el emulator

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

## 2. Crear el entorno Python

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Generar el par RSA local

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

Crea:

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **Nunca subas ni hagas commit de `server\PRIVATE.PEM`.**

## 4. Verificar TCLS y APClient.dat

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

Debes ver:

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

Si aparece el SHA256 original:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

cierra completamente `client.exe` y TCLS y ejecuta:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

SHA256 patched verificado:

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

Después vuelve a ejecutar el diagnostic.

## 5. Redirigir los servicios PH retirados a localhost

Abre **PowerShell como Administrador**:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

Debe quedar:

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

## 6. Iniciar el emulator

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Un preflight correcto incluye:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

Si muestra **FAILED**, no sigas lanzando el cliente. Corrige primero la línea que falló.

---

# PvE

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

`AF_GAME_DIR` debe apuntar a tu carpeta real `Binaries\Win32`.

---

# Lanzar Assault Fire PH

Usa **solo una** opción.

## Opción A — normal TCLS

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

## Opción B — suspended TCLS handoff

Inicia sesión en TCLS y detente en la pantalla **START**, luego:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

**No uses ambos helpers en el mismo lanzamiento.**

---

# Errores comunes

- `.venv python is not recognized` → vuelve al root del repository.
- `AP client initialization failed.` → repite el diagnostic.
- No llega a AUTH → TCLS/RSA/hosts deben estar en **YES**.
- No escribas literalmente `<game-root>`.
- Versiones distintas de **v1.0.0.24** no están soportadas.

---

# Nota sobre el security driver antiguo

El cliente PH original incluye un componente kernel security/anti-cheat antiguo que puede fallar en Windows modernos antes de contactar al emulator.

Este proyecto no proporciona instrucciones para bypass, desactivar, modificar el kernel ni evadir sistemas de security activos.

Consulta [Vital Setup Notes](docs/VITAL_SETUP_NOTES.md).

# Documentación

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Status](docs/STATUS.md)
- [PvE Runtime](docs/PVE_RUNTIME.md)
- [Launcher Errors](docs/LAUNCHER_ERRORS.md)
- [FAQ](docs/FAQ.md)

No subas `PRIVATE.PEM`, contraseñas, credenciales de cuenta ni binarios proprietary del juego.

# License

El código y la documentación originales usan [MIT License](LICENSE).
