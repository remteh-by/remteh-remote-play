# Deckivo — インストールとプレイガイド

Deckivo **0.8.2 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## 準備

0.8.2 は実験的なプレビューです。PS5 とクライアントを同じ家庭内ネットワークに接続します。PS5 で使うユーザーを選び、設定 → システム → リモートプレイ → 有効にする、を設定します。初回登録中は電源を入れたままにしてください。5 GHz Wi-Fi を推奨します。ゲストネットワークは機器を隔離する場合があります。

<a id="android"></a>

## Android

リリースから arm64 APK を取得します。Android 8 以上が必要で、実機テストは Switch OLED / Android 15 です。選択した提供元だけにインストールを許可し、旧版を削除せず上書きします。データを消さず、言語と接続ウィザードを選択します。Bluetooth コントローラーは Android で接続してください。Play Protect は無効化しません。

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.2/Deckivo-0.8.2-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.2)

<a id="macos"></a>

## macOS

Apple Silicon のみです。公式 chiaki-ng を別途インストールし、PS5 を登録して配信を終了します。Mac ZIP を展開し Deckivo.app を ~/Applications に移します。未公証のため macOS のプライバシーとセキュリティで「このまま開く」が必要な場合があります。Gatekeeper 全体を無効化しないでください。Deckivo で chiaki-ng の登録を読み込み、PS5 の IP を入力します。

[Mac ZIP · 0.8.2 b18](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.2/Deckivo-macos-0.8.2-b18.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Switchroot Ubuntu 24.04 ARM64、KDE/X11、FFmpeg 6.1 向け開発者プレビューです。初回は完全なソース、PyQt5、GCC と依存関係が必要です。下のコマンドをソースのルートで実行し、対話式登録を行います。小さい ZIP は既存ランタイムの更新専用です。NVIDIA/FFmpeg ドライバーを置き換えないでください。

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux update ZIP · 0.8.2 b18](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.2/Deckivo-Linux-0.8.2-b18-source.zip) · [Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.2/Deckivo-0.8.2-sources.zip)

## ペアリング

使用するユーザーの Base64 Account ID が必要です。名前やメールではありません。PS5 のリモートプレイ → 機器をリンクで新しい8桁コードを表示し、有効時間内に入力します。任意の ELF ヘルパーのコードは別物です。Linux は対話入力、Mac は chiaki-ng から取り込みます。PIN、鍵、登録ファイルを公開しないでください。

## 操作と画質

まず 720p で試し、不安定ならビットレートを下げるか 30 FPS にします。Android は画面下端から短く上へスワイプすると PS/Touch が表示されます。Linux は Home が PS、Capture がタッチパッドです。音、スティック、トリガー、ボタンを確認してください。切断前にゲームを保存します。配信を閉じてもゲームは終了しません。

## 自動更新

Android はホーム・更新画面が開いている間、通常6時間ごとに GitHub を確認し、従量制でない Wi-Fi で取得できます。OS が確認を求める場合があります。Mac/Linux は署名とハッシュを検証し、配信終了後に再起動します。データは保持してください。旧プライベート版には一度だけ移行が必要です。

[Update details](../UPDATES.md)

## 問題と制限

失敗時は IP、ユーザー、Account ID、新コードとネットワーク隔離を確認します。黒画面では他のクライアントを閉じ、再接続します。正確な検証版は下表を参照。インターネット/VPN、スリープ復帰、長時間プレイと全コントローラー機能は未検証です。Windows、Intel Mac、Linux x64 は予定段階。PS5 の WebKit は修復しません。

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## Deckivo の成長を支援

Deckivo は無料のオープンソースです。支援は新プラットフォームや実機テストに役立ちます。

- Apple Developer ID ($99/yr) — Mac の署名と公証
- Windows 版
- テスト機材の追加：PS5 Pro と携帯端末

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="スマートフォンで読み取る">

すべて無料のまま。支援は任意です。
<!-- SUPPORT:END -->
