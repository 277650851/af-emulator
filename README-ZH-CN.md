# Assault Fire Server Emulator

**语言：** [English](README.md) | [Tagalog](README-TL.md) | [Cebuano](README-CEB.md) | **简体中文** | [更多语言](README-LANGUAGES.md)

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![Engine](https://img.shields.io/badge/Engine-Unreal%20Engine%203-lightgrey)](#)
[![Status](https://img.shields.io/badge/status-preservation%20research-orange)](docs/STATUS.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

这是一个非官方的 **Assault Fire PH** 游戏保存与服务器模拟项目。

目标是在本地/隔离环境中让已经停止运营的 PH 客户端重新可用，用于数字保存、互操作研究、测试和怀旧。

> **支持的客户端：仅 Assault Fire PH v1.0.0.24。**
>
> 其他版本可能使用不同的二进制文件、哈希、数据包结构、TCLS 行为或偏移，目前不受支持。

> 本项目与 Tencent、Level Up! Games 或任何原始权利方无隶属、认可或赞助关系。

---

# ⚠️ 重要 — 点击 START 之前先做这一步

为了获得最稳定的首次启动体验，请先使用 **suspended TCLS launch patcher**。

**现在不要点击 Assault Fire 启动器里的 START。**

完成下面的设置、启动模拟器、登录 `client.exe` / TCLS 并到达正常的 **START** 页面后，在 repository 根目录运行：

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

等待工具显示：

```text
TCLS ARMED
Click START in the Assault Fire launcher now.
```

**只有看到这两行之后再点击 START。**

该工具会自动完成正确的启动顺序：

```text
TCLS creates TGame.exe suspended
        ↓
TCLS finishes the shared-memory handoff
        ↓
required TGame datetime compatibility patch is applied
        ↓
TGame.exe is resumed
```

这样可以避免一个已知的旧版 TGame 启动崩溃：如果兼容补丁还没生效，TGame 就开始运行，游戏可能直接报 Fatal error。

> 使用 `patch_tcls_suspended_launch.py` 时，**同一次启动不要再运行 `patch_tgame_datetime.py`**。suspended-launch helper 已经会自动应用 datetime patch。

如果工具报告 **TGame build/signature mismatch**，请停止，不要强制补丁。目前只支持/测试 Assault Fire PH **v1.0.0.24**。

## 日志级别

你可以让 console 更简洁，同时保留完整的 development DEBUG 日志。

```powershell
$env:AF_LOG_LEVEL = "DEBUG"
```

支持 `DEBUG`、`INFO`（默认）、`WARNING`、`ERROR`。

- `DEBUG` — console 显示全部日志。
- `INFO` — console 隐藏 DEBUG。
- `WARNING` — 只显示 WARNING 和 ERROR。
- `ERROR` — 只显示 ERROR。

**即使 console 没有选择 DEBUG，`server\af_server_live.log` 仍然会保存 DEBUG 以及所有更高级别的日志。** 这样用户使用安静的 console 时，bug report 仍然保留完整诊断信息。

Raw AUTH plaintext/ciphertext 可能包含认证信息，因此不会自动保存。只在受控的本地诊断中使用：`$env:AF_DEBUG_AUTH_HEX = "1"`.

---

## 强制 preflight 启动门

启动 helper 在允许游戏继续之前，服务器 preflight 必须先 **PASS**：

```text
[PREFLIGHT] client root             : <真实游戏目录>
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] game launch gate         : UNLOCKED
```

客户端检查通过后，服务器在绑定所有必需监听端口期间，启动门短暂显示 `LOCKED` 是**正常现象**。此时不要启动游戏；请等待后续出现 `game launch gate : UNLOCKED` 和 `[MAIN] All listeners running.`。

如果出现任何 `NO`、`client root : None` 或 `game launch gate : LOCKED`，**不要点击 START**。服务器不会开放游戏服务监听端口，受支持的启动 helper 会直接显示 `GAME LAUNCH BLOCKED` 并停止。

完整 preflight 报告会写入 `server\af_server_live.log`，机器可读的门状态写入 `runtime\preflight_status.json`。修复问题并重启服务器，只有看到 **UNLOCKED** 后才能继续。

---

# 从这里开始

如果你是第一次使用本项目，请**严格按顺序**执行下面的步骤。

如果某一步显示 **FAILED**，先修复该问题，再继续。不要跳过失败的步骤。

## 你需要准备

- Windows 10/11
- Python 3.10+
- Git
- 你自己的 Assault Fire PH **v1.0.0.24** 游戏文件
- 本仓库

本仓库**不包含**原始游戏客户端、地图、包文件、可执行文件或其他专有游戏资源。

## 重要：先分清两个文件夹

你会使用两个不同的目录。

### 仓库目录

这是包含本 README 以及以下目录的文件夹：

```text
af-emulator
├─ server
├─ tools
├─ docs
├─ tests
└─ README.md
```

仓库相关命令必须从这里运行。

PowerShell 提示符应类似：

```text
PS D:\Something\af-emulator>
```

**不要在 `server\` 目录里面运行这些命令。**

### 游戏根目录

文档中的 `<game-root>` 指你的 Assault Fire PH 安装目录。

例如：

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

那么：

```text
<game-root> = D:\AssaultFirePH
```

**不要真的输入 `<game-root>`。请替换成你的实际游戏目录。**

---

# 快速开始

## 1. 下载模拟器

打开 PowerShell：

```powershell
git clone https://github.com/armangido/af-emulator.git
cd af-emulator
```

如果你下载的是 ZIP，请先解压，然后 `cd` 到解压后的仓库目录。

## 2. 创建 Python 环境

仍然在仓库根目录：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 检查点

此文件现在必须存在：

```text
.venv\Scripts\python.exe
```

如果 PowerShell 提示：

```text
.\.venv\Scripts\python.exe is not recognized
```

通常说明你在错误的目录中。

运行：

```powershell
cd ..
```

直到回到仓库根目录，然后重试。

---

## 3. 生成本地 RSA 密钥对

把 `<game-root>` 替换成你的真实游戏目录：

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "<game-root>\TCLS\config"
```

示例：

```powershell
.\.venv\Scripts\python.exe .\tools\setup\generate_local_rsa_keypair.py --client-config-dir "D:\AssaultFirePH\TCLS\config"
```

它会生成：

```text
server\PRIVATE.PEM
<game-root>\TCLS\config\APClient.dat
```

> **绝对不要上传或提交 `server\PRIVATE.PEM`。**

---

## 4. 检查 TCLS 和 APClient.dat

运行：

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

示例：

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "D:\AssaultFirePH"
```

### 正常情况下应看到

```text
class              : validated raw-PEM-compatible PH TCLS build
exact byte match   : YES
same RSA key       : YES
```

三项都正确后再进入第 5 步。

### 如果 TCLS 是原始/未补丁版本

如果诊断显示 SHA256：

```text
13EAD403452E0F25CF00658369BF4BF5FF34ED1B16027F7833FB27D398386CD1
```

完全关闭 `client.exe` 和 TCLS，然后运行：

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_apclient_raw_pem.py "<game-root>\TCLS\Tenio\TCLS.dll" --apply
```

已验证的补丁版本 SHA256：

```text
3FF351E0ADB594D7544E28DB2E966A6D6EB548E9DF70DAAF4DAF58F2EE438D56
```

补丁工具会创建：

```text
TCLS.dll.bak
```

并拒绝修改未知版本。

补丁完成后，**再次运行诊断工具**。

不要继续，直到看到：

```text
exact byte match   : YES
same RSA key       : YES
```

---

## 5. 把已停用的 PH 服务重定向到 localhost

以**管理员身份**打开 PowerShell。

回到仓库目录并运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\setup\setup_assaultfire_hosts.ps1
```

需要的映射为：

```text
127.0.0.1 tversion.levelupgames.ph
127.0.0.1 tauthproxy.levelupgames.ph
127.0.0.1 tdir.levelupgames.ph
```

一般不需要手动编辑 hosts 文件，使用上面的脚本即可。

---

## 6. 启动模拟器

打开普通 PowerShell 窗口并回到仓库根目录。

设置游戏目录：

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
```

示例：

```powershell
$env:AF_CLIENT_ROOT = "D:\AssaultFirePH"
```

然后启动服务器：

```powershell
.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

### 服务器会在开放端口前检查配置

只要任何必需检查失败，服务器就不会继续启动。

正常输出应包含：

```text
[PREFLIGHT] TCLS validated build    : YES
[PREFLIGHT] APClient exact bytes    : YES
[PREFLIGHT] same RSA key            : YES
[PREFLIGHT] hosts tversion.levelupgames.ph    : YES
[PREFLIGHT] hosts tauthproxy.levelupgames.ph  : YES
[PREFLIGHT] hosts tdir.levelupgames.ph        : YES
[PREFLIGHT] PASS - all required checks succeeded.
```

只有这些检查通过后，监听器才应该启动：

```text
[VERSION] Listening on port 9060
[AUTH] Listening on port 8000
[DIR] Listening on port 9010
[ROLE] Listening on port 65005
[ZONE] Listening on port 65006
```

### 如果 preflight 显示 FAILED

**不要继续反复启动客户端。**

查看失败的那一行，并修复对应问题。

| 错误 | 处理方法 |
| --- | --- |
| `client root is unknown` | 设置 `$env:AF_CLIENT_ROOT = "<game-root>"` |
| `TCLS validated build: NO` | 重新执行第 4 步 |
| `APClient exact bytes: NO` | 重新生成/安装匹配的 `APClient.dat` |
| `same RSA key: NO` | 从第 3 步重新生成 RSA 密钥对 |
| hosts check = `NO` | 用管理员 PowerShell 重新执行第 5 步 |
| `PRIVATE.PEM not found` | 确认 `server\PRIVATE.PEM` 存在 |

---

# PvE 设置

如果要使用 PvE/独立服务器玩法，请在启动 v143b **之前**设置：

```powershell
$env:AF_CLIENT_ROOT = "<game-root>"
$env:AF_GAME_DIR = "<game-root>\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

示例：

```powershell
$env:AF_CLIENT_ROOT = "D:\AssaultFirePH"
$env:AF_GAME_DIR = "D:\AssaultFirePH\Binaries\Win32"
$env:AF_DS_SPAWNER_ENABLED = "1"

.\.venv\Scripts\python.exe .\server\assaultfire_server_v143b.py
```

盘符不重要。请确保 `AF_GAME_DIR` 指向你真实的 **`Binaries\Win32`** 目录。

稳定 PvE 流程：

```text
创建房间
   ↓
预留 DS 容量
   ↓
点击 Start
   ↓
启动房间 bridge
   ↓
收到第一个有效 gameplay packet
   ↓
启动 AFDEV
   ↓
SESSION_READY
   ↓
进入 UE3 gameplay
```

客户端选择的 PvE 地图和设置会传递到独立服务器生命周期。

更多信息：**[PvE Runtime](docs/PVE_RUNTIME.md)**。

---

# 7. 启动 Assault Fire PH

保持模拟器的 PowerShell 窗口开启。

下面两个兼容启动方式**只能选一个**。

## 方式 A — 普通 TCLS 启动

运行：

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tgame_datetime.py
```

然后通过 `client.exe` / TCLS 正常启动。

## 方式 B — suspended TCLS handoff

启动 TCLS、登录，并停在正常的 **START** 页面。

然后运行：

```powershell
.\.venv\Scripts\python.exe .\tools\patches\patch_tcls_suspended_launch.py
```

> suspended-launch helper 已经包含 datetime compatibility patch。
>
> **同一次启动不要同时运行两个 helper。**

---

# 最常见的错误

### “.venv python is not recognized”

你大概率在错误目录里。

错误：

```text
PS D:\Something\af-emulator\server>
```

正确：

```text
PS D:\Something\af-emulator>
```

### “AP client initialization failed.”

重新执行第 4 步：

```powershell
.\.venv\Scripts\python.exe .\tools\patches\diagnose_tcls_apclient.py --client-root "<game-root>"
```

不要猜。检查 TCLS hash、exact byte match 和 RSA 结果。

### 服务器启动了，但客户端没有进入 AUTH

确认：

```text
TCLS validated build = YES
APClient exact bytes = YES
same RSA key = YES
hosts checks = YES
```

然后查看 **[Launcher Errors](docs/LAUNCHER_ERRORS.md)**。

### 我直接复制了 `<game-root>`

它只是占位符。

请替换成真实路径，例如：

```text
D:\AssaultFirePH
```

### 我使用的是其他 Assault Fire 版本

本仓库目前只测试：

```text
Assault Fire PH v1.0.0.24
```

其他版本不能保证工作，需要额外研究。

---

# 旧版安全驱动说明

原始 PH 客户端包含为旧版 Windows 环境设计的内核级安全/反作弊组件。

在现代 Windows 上，它可能在**连接模拟器之前**就造成启动失败、崩溃或驱动初始化错误。

如果客户端在出现正常 VERSION/AUTH 流量之前就失败，那么问题可能在客户端/操作系统兼容层，而不是服务器模拟器。

本项目不提供绕过、禁用、内核修改或针对活动安全系统的规避说明。

请查看 **[Vital Setup Notes](docs/VITAL_SETUP_NOTES.md)**。

---

# 当前可用功能

当前公开基线为 **v143b**。

已工作或已集成的部分包括：

- VERSION / AUTH / DIR / ROLE / ZONE 本地后端流程
- 现有/本地 profile 登录
- 动态房间支持
- shared-room 多人支持工作
- PvE 独立服务器分配和生命周期
- 客户端选择的 PvE 地图/设置传递
- lazy AFDEV 启动
- v48 AFDEV loader
- v9 multi-peer UDP bridge
- zero-DSKey readiness path
- inventory/shop/profile 保存相关工作

部分功能仍处于未完成或验证阶段，例如首次 nickname/account 流程以及部分社交/进度系统。

查看 **[Project Status](docs/STATUS.md)** 获取当前状态表。

---

# 故障排查

| 问题 | 文档 |
| --- | --- |
| 第一次设置 / 不知道下一步 | [Getting Started](docs/GETTING_STARTED.md) |
| AP/TCLS/TGame 启动错误 | [Launcher Errors](docs/LAUNCHER_ERRORS.md) |
| TCLS → TGame handoff 问题 | [Launch Requirements](docs/LAUNCH_REQUIREMENTS.md) |
| PvE / AFDEV / 独立服务器 | [PvE Runtime](docs/PVE_RUNTIME.md) |
| 旧驱动 / 现代 Windows 问题 | [Vital Setup Notes](docs/VITAL_SETUP_NOTES.md) |
| 不确定某功能是否实现 | [Project Status](docs/STATUS.md) |
| 常见问题 | [FAQ](docs/FAQ.md) |

报告 bug 时请提供：

- 完整错误文字
- 出错时所在步骤
- 运行的命令
- 最后几行相关服务器/客户端日志
- 客户端版本
- 如果涉及 TCLS/TGame，请提供相关哈希

**不要**上传 `PRIVATE.PEM`、密码、账号凭据或专有游戏二进制文件。

---

# 文档

| 文档 | 用途 |
| --- | --- |
| [Getting Started](docs/GETTING_STARTED.md) | 完整首次设置 |
| [Project Status](docs/STATUS.md) | 已实现 / 部分实现 / 计划功能 |
| [PvE Runtime](docs/PVE_RUNTIME.md) | PvE 和独立服务器流程 |
| [Launch Requirements](docs/LAUNCH_REQUIREMENTS.md) | TCLS → TGame 要求 |
| [Launcher Errors](docs/LAUNCHER_ERRORS.md) | 已知 AP/TCLS/TGame 错误 |
| [Architecture](docs/ARCHITECTURE.md) | 端口、服务和数据流 |
| [Research Findings](docs/RESEARCH_FINDINGS.md) | 已验证协议/运行时发现 |
| [FAQ](docs/FAQ.md) | 常见问题 |
| [Contributing](CONTRIBUTING.md) | 贡献修复和研究 |

---

# 项目范围

本仓库包含原创模拟器代码、文档和研究工具。

请不要提交：

- 原始游戏 EXE 或 DLL
- 地图、`.upk`、`.udk`、音频、纹理或其他专有资源
- 私钥
- 密码、token、cookie 或账号凭据
- 包含专有或个人数据的原始内存转储
- 你无权重新分发的文件

用户必须自行并合法地获取所需的原始游戏文件。

---

# License

本仓库中的原创代码和文档采用 [MIT License](LICENSE)。

该许可证不授予对 Assault Fire、原始客户端、可执行文件、DLL、地图、包文件、美术、音频、商标或其他第三方材料的权利。
