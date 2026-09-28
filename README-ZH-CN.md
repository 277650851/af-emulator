# Assault Fire Server Emulator

**语言：** [English](README.md) | [Tagalog](README-TL.md) | [Cebuano](README-CEB.md) | **简体中文** | [更多语言](README-LANGUAGES.md)

这是一个用于保存 **Assault Fire PH** 并模拟其服务器的非官方项目。本项目及第三方运营的服务器均与 Tencent、Level Up! Games 或原始权利方无关联，也未获得其赞助或认可。社区服务器由各自运营者独立管理。

> **仅支持并测试此版本：** Assault Fire PH **v1.0.0.24**。本仓库不包含游戏文件。你必须自行拥有游戏文件。

## 最简单的启动方式

1. 将整个 `af-emulator` 文件夹放入 Assault Fire PH 游戏目录。
2. 右键点击 `START_ASSAULT_FIRE.ps1`，选择 **Run with PowerShell**。Windows 请求管理员权限时请允许。
3. 启动脚本会检查版本和配置、准备本地密钥，然后启动服务器、启动辅助程序和游戏客户端。
4. 在客户端登录。出现 **START** 按钮后，点击继续。

正常的一键流程不需要你手动启动服务器或补丁工具。脚本不会下载或分发游戏文件，只使用你本机已有的文件。如果版本不匹配，或无法验证 `TGame.exe` / `TCLS.dll` 的签名，请停止操作，不要强行打补丁。启动游戏前，启动器会将经过验证的日期时间补丁永久写入 `TGame.exe`，并先保存逐字节一致的备份 `TGame.exe.bak`。如果没有安全代码空间，只有在 PE 头部有空闲节表项时才会添加一个小型可执行节 `.afdt`；否则不会修改文件。

## 手动设置和开发者说明

所有详细步骤和准确命令请查看[完整英文指南](README.md)。需要 Windows、Python 3.10 或更高版本，以及你自己拥有的受支持游戏版本。手动设置时，等待预检显示 `UNLOCKED`。手动启动游戏时，辅助程序显示 `TCLS ARMED` 之前不要点击 **START**。`--server-only` 仅用于托管服务器，不会解锁本机游戏启动。

## 状态与求助

当前公开稳定基线为 **v143b**。VERSION、AUTH、DIR、ROLE、ZONE 流程、房间管理和 PvE 对局流程已可用。首次创建昵称/账号以及部分社交和进度功能仍在开发中。客户端初始 AP 同步目前仍使用临时本地方案。

寻求帮助时，请提供错误截图、你执行到的步骤、实际运行的准确命令、`server/af_server_live.log` 和游戏版本。**请勿发送** `PRIVATE.PEM`、密码、账号凭据、令牌或原版游戏文件。

- [项目状态](docs/STATUS.md) · [启动器错误](docs/LAUNCHER_ERRORS.md) · [重要设置说明](docs/VITAL_SETUP_NOTES.md) · [文档索引](docs/README.md)
- [所有语言的 README](README-LANGUAGES.md)

**许可证：** MIT。
