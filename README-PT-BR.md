# Assault Fire Server Emulator

**Idioma:** [English](README.md) | **Português (Brasil)** | [Outros idiomas](README-LANGUAGES.md)

Projeto não oficial de preservação e emulação de servidor para **Assault Fire PH**.

O objetivo é tornar o cliente PH descontinuado utilizável novamente em um ambiente local/isolado para preservação, pesquisa de interoperabilidade, testes e nostalgia.

> **Cliente suportado: somente Assault Fire PH v1.0.0.24.**
>
> Outras versões podem ter binários, hashes, packet layouts, comportamento TCLS ou offsets diferentes e não são suportadas no momento.

---

# ⚠️ IMPORTANTE — antes de clicar em START

Para o primeiro launch mais confiável, use primeiro o **suspended TCLS launch patcher**.

**Não clique em START** ainda no launcher do Assault Fire.

Depois de terminar o setup abaixo, iniciar o emulator, fazer login pelo `client.exe` / TCLS e chegar à tela normal de **START**, execute a partir da raiz do repository:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

Espere aparecer:

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

**Só então clique em START.**

O helper executa automaticamente a sequência correta:

```text
TCLS creates TGame.exe suspended
        ↓
TCLS finishes the shared-memory handoff
        ↓
required TGame datetime compatibility patch is applied
        ↓
TGame.exe is resumed
```

Isso ajuda a evitar um crash conhecido do TGame antigo quando o jogo começa a executar antes de o compatibility patch estar ativo.

> Ao usar `patch_tcls_suspended_launch.py`, **não execute também `patch_tgame_datetime.py` no mesmo launch**. O suspended-launch helper já aplica o datetime patch.

Se aparecer **TGame build/signature mismatch**, pare e não force o patch. Atualmente somente Assault Fire PH **v1.0.0.24** é suportado/testado.

## Logging level

Você pode deixar o console mais limpo sem perder os logs de desenvolvimento.

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

Níveis: `DEBUG`, `INFO` (padrão), `WARNING`, `ERROR`.

- `DEBUG` — mostra tudo no console.
- `INFO` — esconde DEBUG do console.
- `WARNING` — mostra apenas WARNING e ERROR.
- `ERROR` — mostra apenas ERROR.

**Mesmo que o console não esteja em DEBUG, `server\af_server_live.log` sempre salva DEBUG e todos os níveis superiores.** Assim os detalhes necessários para bugs e development continuam disponíveis.

Raw AUTH plaintext/ciphertext não é salvo automaticamente porque pode conter material de autenticação. Use apenas em diagnostic local controlado com `$env:AF_DEBUG_AUTH_HEX = "1"`.

---

## Mandatory preflight launch gate

Antes de o helper permitir que o jogo continue, o server preflight precisa estar em **PASS**:

```text
[PREFLIGHT] client root             : <pasta real do jogo>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

É **normal** o gate ficar temporariamente `LOCKED` depois que os client checks passam enquanto o servidor faz bind de todos os listeners obrigatórios. Não faça launch ainda. Espere `game launch gate : UNLOCKED` e `[MAIN] All listeners running.`

Se aparecer qualquer `NO`, `client root : None` ou `game launch gate : LOCKED`, **não clique em START**. Os listeners do servidor não abrem e os launch helpers suportados param com `GAME LAUNCH BLOCKED`.

O preflight completo é salvo em `server\af_server_live.log` e o estado machine-readable do gate em `runtime\preflight_status.json`. Corrija o problema, reinicie o servidor e prossiga somente quando estiver **UNLOCKED**.

---

# Comece aqui

Se esta é sua primeira vez usando o projeto, siga os passos **na ordem**.

Se algum passo mostrar **FAILED**, corrija esse problema antes de continuar.

## Você precisa de

- Windows 10/11
- Python 3.10+
- Git
- sua própria instalação de Assault Fire PH **v1.0.0.24**
- este repository

Este repository não inclui o cliente original, mapas, packages, executáveis ou outros arquivos proprietary do jogo.

## Diferencie as duas pastas

### Pasta do repository

Execute os comandos na pasta que contém:

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

O PowerShell deve parecer com:

```text
PS D:\Something\af-emulator>
```

**Não execute os comandos dentro de `server\`.**

### Game root

`<game-root>` significa a pasta de instalação do Assault Fire PH.

Exemplo:

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

**Não digite `<game-root>` literalmente. Substitua pelo caminho real.**

---

# Início rápido

## 1. Baixar o emulator

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

## 2. Criar o ambiente Python

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Gerar o par RSA local

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

Isso cria:

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **Nunca faça upload ou commit de `server\PRIVATE.PEM`.**

## 4. Verificar TCLS e APClient.dat

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

Você deve ver:

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

Se aparecer o SHA256 original:

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

feche completamente `client.exe` e TCLS e execute:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

SHA256 patched verificado:

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

Execute o diagnostic novamente depois do patch.

## 5. Redirecionar os serviços PH antigos para localhost

Abra **PowerShell como Administrador**:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

Necessário:

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

## 6. Iniciar o emulator

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

Um preflight saudável mostra:

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

Se mostrar **FAILED**, não continue abrindo o client. Corrija a linha que falhou.

---

# PvE

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

`AF_GAME_DIR` deve apontar para sua pasta real `Binaries\Win32`.

---

# Abrir Assault Fire PH

Use **apenas uma** opção.

## Opção A — normal TCLS

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

## Opção B — suspended TCLS handoff

Entre no TCLS e pare na tela **START**, depois:

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

**Não use os dois helpers no mesmo launch.**

---

# Erros comuns

- `.venv python is not recognized` → volte para o root do repository.
- `AP client initialization failed.` → repita o diagnostic.
- Não chega ao AUTH → TCLS/RSA/hosts devem estar em **YES**.
- Não digite `<game-root>` literalmente.
- Versões diferentes de **v1.0.0.24** não são suportadas.

---

# Nota sobre o security driver antigo

O cliente PH original possui um componente kernel security/anti-cheat antigo que pode falhar em Windows modernos antes de chegar ao emulator.

Este projeto não fornece instruções de bypass, desativação, modificação de kernel ou evasão de security ativo.

Consulte [Vital Setup Notes](docs/VITAL_SETUP_NOTES.md).

# Documentação

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Status](docs/STATUS.md)
- [PvE Runtime](docs/PVE_RUNTIME.md)
- [Launcher Errors](docs/LAUNCHER_ERRORS.md)
- [FAQ](docs/FAQ.md)

Não faça upload de `PRIVATE.PEM`, senhas, credenciais de conta ou binários proprietary do jogo.

# License

Código e documentação originais usam [MIT License](LICENSE).
