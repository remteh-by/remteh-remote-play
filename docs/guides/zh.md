# Deckivo — 安装与游玩指南

Deckivo **0.8.5 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## 开始之前

0.8.5 是实验性预览版。请先让 PS5 与客户端连接同一家庭网络。在 PS5 选择要使用的用户，打开设置 → 系统 → 远程游玩 → 启用远程游玩。首次配对时保持主机开机。建议使用 5 GHz Wi-Fi；访客网络可能隔离设备。应用不会安装 Android/Linux 或修改 PS5 固件。

<a id="android"></a>

## Android

从下方版本页面下载 arm64 APK。最低需要 Android 8；实际设备测试为 Switch OLED / Android 15。仅为选定的安装来源授权。直接覆盖旧版，不要卸载或清除数据，以保留配对。选择语言并打开连接向导，在 Android 蓝牙设置中连接手柄。不要关闭 Play Protect。

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.5/Deckivo-0.8.5-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.5)

<a id="macos"></a>

## macOS

本预览版仅适用于 Apple Silicon。另行安装官方 chiaki-ng，在其中注册 PS5 并结束串流。解压 Mac ZIP，把 Deckivo.app 放入 ~/Applications。应用未经过公证，macOS 可能要求在隐私与安全性中选择“仍要打开”；不要全局关闭 Gatekeeper。在 Deckivo 设置中导入 chiaki-ng 注册信息并输入主机 IP。保留 chiaki-ng，它提供串流引擎。

[Mac ZIP · 0.8.5 b21](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.5/Deckivo-macos-0.8.5-b21.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

开发者预览针对 Switchroot Ubuntu 24.04 ARM64、KDE/X11 和 FFmpeg 6.1。首次安装需要完整源码、PyQt5、GCC 及依赖。请从源码根目录执行下方命令，再运行交互式配对。小型 Linux ZIP 只更新已有运行环境。不要替换 NVIDIA/FFmpeg 驱动；固定版本软件包不可用时应停止。

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux update ZIP · 0.8.5 b21](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.5/Deckivo-Linux-0.8.5-b21-source.zip) · [Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.5/Deckivo-0.8.5-sources.zip)

## 配对与首次连接

需要对应用户的 Base64 Account ID，不是昵称或邮箱。在 PS5 打开远程游玩 → 连接设备，在计时结束前输入新的八位码。可选 ELF 助手的验证码与此不同。Linux 脚本交互式读取信息；Mac 导入 chiaki-ng 注册。不要公开 PIN、注册文件或密钥。普通远程游玩不需要运行 PS5 助手。

## 操作与画质

先使用 720p；网络不稳定时降低码率或改为 30 FPS。这些是请求参数，并非性能承诺。Android 从底部边缘短划向上显示 PS/Touch；Linux 的 Home 对应 PS，Capture 对应触摸板。检查声音、摇杆、扳机和按钮。断开前保存游戏；结束串流不会关闭游戏。

## 自动更新

Android 在主界面或更新界面打开时检查 GitHub，通常每六小时一次，可在不限流量的 Wi-Fi 下载。系统仍可能要求安装确认。Mac/Linux 验证元数据签名和文件哈希，并等待串流结束后重启。不要删除应用数据。旧私有构建需要一次性迁移；休眠或关闭应用不代表持续后台更新。

[Update details](../UPDATES.md)

## 故障排查与限制

配对失败时检查 IP、用户、Account ID、新验证码及网络隔离。黑屏时关闭其他远程游玩客户端，再重新连接或降低画质。具体测试版本见下表。互联网/VPN、休眠唤醒、长时间游玩及所有手柄功能尚未验证。Windows、Intel Mac 和桌面 Linux x64 仍在计划中。Deckivo 不修复 PS5 WebKit。

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## 帮助 Deckivo 成长

Deckivo 免费开源。支持将用于新平台、签名和真实设备测试。

- Apple Developer ID ($99/yr) — Mac 签名与公证
- Windows 版本
- 更多测试设备：PS5 Pro 和掌机

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="用手机扫描">

所有功能保持免费，支持完全自愿。
<!-- SUPPORT:END -->
