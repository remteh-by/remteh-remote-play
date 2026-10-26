# Deckivo — 설치 및 플레이 안내

Deckivo **0.8.6 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## 시작하기 전에

0.8.6은 실험용 미리 보기입니다. PS5와 클라이언트를 같은 가정 네트워크에 연결하세요. PS5에서 사용할 프로필을 고르고 설정 → 시스템 → 리모트 플레이 → 활성화를 선택합니다. 첫 등록 중에는 콘솔을 켜 두세요. 5 GHz Wi-Fi를 권장하며 게스트 네트워크는 기기를 격리할 수 있습니다.

<a id="android"></a>

## Android

릴리스에서 arm64 APK를 받으세요. Android 8 이상이 필요하며 실기기 검증은 Switch OLED / Android 15입니다. 선택한 출처에만 설치 권한을 허용하세요. 기존 앱을 삭제하거나 데이터를 지우지 말고 덮어 설치합니다. 언어와 연결 마법사를 선택하고 Android Bluetooth에서 게임패드를 연결하세요. Play Protect를 끄지 마세요.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.6/Deckivo-0.8.6-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.6)

<a id="macos"></a>

## macOS

Apple Silicon 전용입니다. 공식 chiaki-ng를 별도로 설치하고 PS5를 등록한 뒤 스트림을 닫으세요. Mac ZIP을 풀고 Deckivo.app을 ~/Applications로 옮깁니다. 공증되지 않은 앱이므로 개인정보 보호 및 보안에서 “확인 없이 열기”가 필요할 수 있습니다. Gatekeeper 전체를 끄지 마세요. Deckivo에서 chiaki-ng 등록을 가져오고 콘솔 IP를 입력합니다.

[Mac ZIP · 0.8.6 b22](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.6/Deckivo-macos-0.8.6-b22.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Switchroot Ubuntu 24.04 ARM64, KDE/X11, FFmpeg 6.1용 개발자 미리 보기입니다. 처음 설치하려면 전체 소스, PyQt5, GCC와 의존성이 필요합니다. 소스 루트에서 아래 명령과 대화형 등록을 실행하세요. 작은 ZIP은 기존 런타임 업데이트 전용입니다. NVIDIA/FFmpeg 드라이버를 교체하지 마세요.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux update ZIP · 0.8.6 b22](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.6/Deckivo-Linux-0.8.6-b22-source.zip) · [Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.6/Deckivo-0.8.6-sources.zip)

## 기기 등록

닉네임이나 이메일이 아닌 해당 프로필의 Base64 Account ID가 필요합니다. PS5 리모트 플레이 → 기기 연결에서 새 8자리 코드를 받고 제한 시간 안에 입력하세요. 선택 사항인 ELF 도우미의 코드는 별개입니다. Linux는 대화형 입력, Mac은 chiaki-ng 가져오기를 사용합니다. PIN, 키, 등록 파일을 공개하지 마세요.

## 조작과 품질

720p부터 시작하고 불안정하면 비트레이트를 낮추거나 30 FPS로 바꾸세요. Android에서 아래 가장자리를 짧게 위로 밀면 PS/Touch가 나옵니다. Linux의 Home은 PS, Capture는 터치패드입니다. 소리, 스틱, 트리거와 버튼을 확인하세요. 연결 종료 전에 저장하세요. 스트림 종료는 게임을 닫지 않습니다.

## 자동 업데이트

Android는 홈/업데이트 화면이 열린 동안 보통 6시간마다 GitHub를 확인하며 무제한 Wi-Fi에서 다운로드할 수 있습니다. OS가 설치 확인을 요구할 수 있습니다. Mac/Linux는 서명과 해시를 검증하고 스트림이 끝난 뒤 재시작합니다. 데이터를 유지하세요. 예전 비공개 빌드는 일회성 전환이 필요합니다.

[Update details](../UPDATES.md)

## 문제와 제한

실패하면 IP, 프로필, Account ID, 새 코드와 네트워크 격리를 확인하세요. 검은 화면이면 다른 클라이언트를 닫고 다시 연결하세요. 정확한 검증 버전은 아래에 있습니다. 인터넷/VPN, 절전 해제, 장시간 플레이와 모든 컨트롤러 기능은 미검증입니다. Windows, Intel Mac, Linux x64는 계획 단계입니다. PS5 WebKit은 고치지 않습니다.

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## Deckivo의 성장을 도와주세요

Deckivo는 무료 오픈 소스입니다. 후원은 새 플랫폼과 실제 기기 테스트에 도움이 됩니다.

- Apple Developer ID ($99/yr) — Mac 서명 및 공증
- Windows 버전
- 테스트 기기 추가: PS5 Pro 및 휴대용 기기

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="휴대폰으로 스캔">

모두 무료로 유지됩니다. 후원은 선택 사항입니다.
<!-- SUPPORT:END -->
