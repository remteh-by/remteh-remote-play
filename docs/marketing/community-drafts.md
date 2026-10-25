# Community drafts — not posted

Use the published release test matrix when posting; do not advertise untested
Internet play, Windows, or a paid support service. Follow each community's rules.

## r/SwitchHacks · English

**Deckivo 0.6.1 preview: open-source PS5 Remote Play on Switchroot Android**

I've been adapting Chiaki / chiaki-ng / Android Extended for my Switch OLED.
Deckivo adds a shared graphite/lime UI, controller setup tools, local pairing,
hidden PS/Touch controls, and verified in-app updates. The same project has an
Apple Silicon Mac frontend and an experimental Switchroot Ubuntu ARM64 client.

0.6.1 adds locally generated support QR codes, offline license texts, localized
updater states and desktop startup rollback. It does not install Switchroot or
modify the PS5. Start on the same home network and use your own console/profile.

Exact hardware/builds and remaining tests:
https://github.com/remteh-by/remteh-remote-play/blob/main/docs/TESTED.md
Source and preview: https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.2
Upstream credit: Chiaki, chiaki-ng, Android Extended. Optional support funds signing and hardware; everything stays free.

## GBAtemp / Switchroot · English

**Deckivo — a PS5 Remote Play frontend for Switchroot Android and Ubuntu**

Deckivo is a modified Chiaki-family client, not a new Remote Play protocol.
The Android ARM64 APK targets Android 8+; device work used Switch OLED Android 15.
The Ubuntu developer target is Switchroot 24.04 ARM64 with KDE/X11 and its matching
FFmpeg packages. The Linux upgrade archive needs an existing runtime.
GameSir G8+ is in the earlier physical test history; check the release matrix for
what has actually been rerun. Internet/VPN and long sessions remain owner tests.

Guides in 16 languages: https://remteh-by.github.io/remteh-remote-play/
Source: https://github.com/remteh-by/remteh-remote-play

## XDA · English

**[APP][OPEN SOURCE][PREVIEW] Deckivo 0.6.1 — PS5 Remote Play / ARM64**

A Chiaki-derived Remote Play client with an Android connection wizard, gamepad
calibration, explicit language picker, diagnostics and a verified GitHub updater.
No Deckivo account is needed. Registration stays on the client; do not post it in
bug reports. Keep Play Protect enabled. Download the signed APK over the previous
installation to retain pairing. macOS and Switchroot Ubuntu have separate guides.

Release / full corresponding source / hashes:
https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.2
License: AGPL-3.0 with the retained upstream OpenSSL permission.

## 4PDA · Русский

**Deckivo 0.6.1 preview — своя PS5 на Switch OLED под Android**

Это доработка Chiaki / chiaki-ng / Android Extended: новый интерфейс, мастер
подключения, проверка геймпада, скрываемые кнопки PS/Touch и обновления с проверкой
подписи APK. Есть отдельный клиент для Apple Silicon Mac и тестовая версия Ubuntu
на Switch. Windows пока в планах.

В 0.6.1 добавлены крупные QR для добровольной поддержки, офлайн-лицензии,
переведённые статусы обновления и откат desktop при неудачном старте.
Начинать надо в общей локальной сети. Нужны свой Account ID выбранного профиля
и свежий код Remote Play. Прошивку PS5 приложение не меняет.

Инструкция и точные проверенные версии:
https://remteh-by.github.io/remteh-remote-play/ru/
Исходники и файлы: https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.2
Длительную игру и подключение через интернет не выдаём за завершённые тесты.

## Хабр · технический черновик

**От Chiaki к Deckivo: общий интерфейс, обновления с подписью и Tegra-декодер**

Мы не писали протокол PS5 Remote Play заново. Его транспорт и основной видеостек
пришли из Chiaki, chiaki-ng и Android Extended. Исходная история и лицензии
сохранены. Наш слой — Android-мастер и управление, общий Qt-интерфейс,
диагностика, упаковка и доставка обновлений.

### Как не сломать обновление

Android берёт дескриптор из GitHub Releases и проверяет package name, монотонный
versionCode, minSdk, размер, SHA-256 и сертификат APK. Сам установщик остаётся
системным: разрешение источника и Play Protect не обходятся.

Mac и Linux используют отдельный RSA-подписанный индекс. Проверка PKCS#1 v1.5
SHA-256 в 0.6.1 написана на Python: строгий SPKI/DER, размер подписи по модулю,
`pow(sig,e,n)`, точный padding/DigestInfo и сравнение целого блока. Это снимает
зависимость runtime от внешнего openssl. Приватный ключ в приложение не входит.
После замены файлов новый процесс должен подтвердить transaction и PID за 120
секунд. Подтверждение пишет работающий event loop после показа окна и загрузки
настроек/регистрации и проверки движка. При сбое живой новый процесс сначала
останавливается; только затем восстанавливается старый bundle или backup Linux.

### Адаптер Tegra и геймпад

Switchroot Ubuntu требует своего совместимого FFmpeg/NVIDIA-стека; смена драйверов
ради пакета — плохой способ установки. Адаптер использует установленный стек,
передаёт реальный ввод и отделяет запрашиваемый FPS от измеренных декодером
показателей. На Mac видеодвижком остаётся отдельно установленный chiaki-ng.

### Где заканчивается проверка

Сборка и unit-тесты не доказывают долгую игру на железе. Таблица содержит точные
версии, отдельные результаты OTA, изображения/звука/управления и непроверенные
сценарии. Локальный стрим и удалённая игра через интернет — разные тесты.

Код: https://github.com/remteh-by/remteh-remote-play
Состояние приёмки: https://github.com/remteh-by/remteh-remote-play/blob/main/docs/TESTED.md
