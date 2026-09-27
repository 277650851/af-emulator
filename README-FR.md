# Assault Fire Server Emulator

**Langue :** [English](README.md) | **Français** | [Autres langues](README-LANGUAGES.md)

Projet non officiel de préservation et d'émulation de serveur pour **Assault Fire PH**.

Le but est de rendre le client PH retiré à nouveau utilisable dans un environnement local/isolé pour la préservation, la recherche d'interopérabilité, les tests et la nostalgie.

> **Client pris en charge : Assault Fire PH v1.0.0.24 uniquement.**
>
> Les autres versions peuvent utiliser des binaires, hashes, packet layouts, comportements TCLS ou offsets différents et ne sont pas prises en charge actuellement.

---

# ⚠️ IMPORTANT — avant de cliquer sur START

Pour le premier lancement le plus fiable, utilisez d'abord le **suspended TCLS launch patcher**.

**Ne cliquez pas encore sur START** dans le launcher Assault Fire.

Après avoir terminé la configuration ci-dessous, démarré l'emulator, vous être connecté via `client.exe` / TCLS et atteint l'écran normal **START**, exécutez depuis la racine du repository:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

Attendez l'affichage:

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

**Cliquez seulement ensuite sur START.**

Le helper effectue automatiquement la séquence correcte:

```text
TCLS creates TGame.exe suspended
        ↓
TCLS finishes the shared-memory handoff
        ↓
required TGame datetime compatibility patch is applied
        ↓
TGame.exe is resumed
```

Cela aide à éviter un crash de démarrage connu de l'ancien TGame lorsque le jeu commence à s'exécuter avant que le compatibility patch soit actif.

> Avec `patch_tcls_suspended_launch.py`, **n'exécutez pas aussi `patch_tgame_datetime.py` pour le même lancement**. Le suspended-launch helper applique déjà le datetime patch.

Si **TGame build/signature mismatch** apparaît, arrêtez-vous et ne forcez pas le patch. Seul Assault Fire PH **v1.0.0.24** est actuellement pris en charge/testé.

## Logging level

Vous pouvez rendre le console plus silencieux sans perdre les logs de développement.

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

Niveaux: `DEBUG`, `INFO` (par défaut), `WARNING`, `ERROR`.

- `DEBUG` — affiche tout dans le console.
- `INFO` — masque DEBUG dans le console.
- `WARNING` — seulement WARNING et ERROR.
- `ERROR` — seulement ERROR.

**Même si le console n'est pas en DEBUG, `server\af_server_live.log` enregistre toujours DEBUG et tous les niveaux supérieurs.** Les détails nécessaires pour les bugs et le development restent disponibles.

Raw AUTH plaintext/ciphertext n'est pas enregistré automatiquement car il peut contenir du matériel d'authentification. Utilisez-le uniquement pour un diagnostic local contrôlé avec `$env:AF_DEBUG_AUTH_HEX = "1"`.

---

## Mandatory preflight launch gate

Avant que le helper autorise le jeu à continuer, le preflight du serveur doit être en **PASS**:

```text
[PREFLIGHT] client root             : <vrai dossier du jeu>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

Il est **normal** que le gate reste temporairement `LOCKED` après la réussite des client checks pendant que le serveur bind tous les listeners requis. Ne lancez pas encore le jeu. Attendez `game launch gate : UNLOCKED` et `[MAIN] All listeners running.`

Si un `NO`, `client root : None` ou `game launch gate : LOCKED` apparaît, **ne cliquez pas sur START**. Les listeners du serveur ne s'ouvrent pas et les launch helpers pris en charge s'arrêtent avec `GAME LAUNCH BLOCKED`.

Le rapport preflight complet est enregistré dans `server\af_server_live.log` et l'état machine-readable du gate dans `runtime\preflight_status.json`. Corrigez le problème, redémarrez le serveur et continuez uniquement lorsque le gate est **UNLOCKED**.

---

# Commencez ici

Si c'est votre première utilisation, suivez les étapes **dans l'ordre**.

Si une étape affiche **FAILED**, corrigez ce problème avant de continuer.

## Prérequis

- Windows 10/11
- Python 3.10+
- Git
- votre propre installation Assault Fire PH **v1.0.0.24**
- ce repository

Le repository ne contient pas le client original, les maps, packages, exécutables ou autres fichiers proprietary du jeu.

## Distinguez les deux dossiers

### Dossier du repository

Exécutez les commandes depuis le dossier contenant :

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

PowerShell devrait ressembler à :

```text
PS D:\Something\af-emulator>
```

**N'exécutez pas les commandes depuis `server\`.**

### Game root

`<game-root>` représente le dossier d'installation d'Assault Fire PH.

Exemple :

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

**Ne tapez pas `<game-root>` littéralement. Remplacez-le par votre chemin réel.**

---

# Démarrage rapide

## 1. Télécharger l'emulator

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

## 2. Créer l'environnement Python

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Générer la paire RSA locale

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

Cela crée :

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **N'uploadez et ne committez jamais `server\PRIVATE.PEM`.**

## 4. Vérifier TCLS et APClient.dat

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

Vous devez voir :

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

Si le SHA256 original apparaît :

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

fermez complètement `client.exe` et TCLS puis exécutez :

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

SHA256 patched vérifié :

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

Relancez ensuite le diagnostic.

## 5. Rediriger les anciens services PH vers localhost

Ouvrez **PowerShell en tant qu'Administrateur** :

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

Requis :

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

## 6. Démarrer l'emulator

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Un preflight correct affiche :

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

Si vous voyez **FAILED**, ne continuez pas à lancer le client. Corrigez d'abord la ligne en erreur.

---

# PvE

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

`AF_GAME_DIR` doit pointer vers votre vrai dossier `Binaries\Win32`.

---

# Lancer Assault Fire PH

Utilisez **une seule** option.

## Option A — normal TCLS

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

## Option B — suspended TCLS handoff

Connectez-vous dans TCLS et arrêtez-vous sur l'écran **START**, puis :

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

**N'utilisez pas les deux helpers pour le même lancement.**

---

# Erreurs courantes

- `.venv python is not recognized` → revenez à la racine du repository.
- `AP client initialization failed.` → relancez le diagnostic.
- Pas d'AUTH → TCLS/RSA/hosts doivent tous être **YES**.
- Ne tapez pas `<game-root>` littéralement.
- Les versions autres que **v1.0.0.24** ne sont pas prises en charge.

---

# Note sur l'ancien security driver

Le client PH original contient un composant kernel security/anti-cheat ancien pouvant échouer sur Windows moderne avant de contacter l'emulator.

Ce projet ne fournit pas d'instructions de bypass, désactivation, modification kernel ou contournement de security actif.

Voir [Vital Setup Notes](docs/VITAL_SETUP_NOTES.md).

# Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Status](docs/STATUS.md)
- [PvE Runtime](docs/PVE_RUNTIME.md)
- [Launcher Errors](docs/LAUNCHER_ERRORS.md)
- [FAQ](docs/FAQ.md)

N'uploadez pas `PRIVATE.PEM`, mots de passe, identifiants de compte ou binaires proprietary du jeu.

# License

Le code et la documentation originaux utilisent la [MIT License](LICENSE).
