# Deckivo — встановлення та гра

Deckivo **0.6.0 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Перед початком

Це експериментальна версія 0.6.0. Під’єднайте PS5 і клієнт до однієї домашньої мережі. На PS5 увійдіть у потрібний профіль: Налаштування → Система → Дистанційна гра → Увімкнути. Для першого підключення залиште консоль увімкненою. Гостьова мережа може ізолювати пристрої; бажано використовувати 5 ГГц.

## Android

Завантажте arm64 APK з випуску. Потрібен Android 8+; перевірено Switch OLED з Android 15. Дозвольте встановлення лише вибраному джерелу. Встановлюйте поверх старої версії без видалення даних. Виберіть мову, відкрийте майстер підключення та під’єднайте Bluetooth-контролер у налаштуваннях Android. Не вимикайте Play Protect.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-0.6.0-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.6.0)

<a id="macos"></a>

## macOS

Лише Apple Silicon. Окремо встановіть chiaki-ng, прив’яжіть PS5 та закрийте його трансляцію. Розпакуйте ZIP Mac і перенесіть Deckivo.app до ~/Applications. Програма не має нотаризації: macOS може вимагати «Усе одно відкрити» у налаштуваннях безпеки. Не вимикайте Gatekeeper. У Deckivo імпортуйте реєстрацію chiaki-ng і вкажіть IP консолі.

[Mac ZIP · 0.6.0 b9](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-macos-0.6.0-b9.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Розробницька збірка для Switchroot Ubuntu 24.04 ARM64, KDE/X11 та FFmpeg 6.1. Для першого встановлення потрібні повні вихідні коди, PyQt5, GCC і залежності. Виконайте команди нижче. Малий ZIP — лише оновлення наявного runtime. Не замінюйте драйвери заради запуску.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux technical requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-0.6.0-sources.zip)

## Прив’язування

Використовуйте Base64 Account ID потрібного профілю, а не нік чи пошту. На PS5 відкрийте Дистанційна гра → Прив’язати пристрій та введіть свіжий восьмизначний код до завершення таймера. Код локального ELF-помічника відрізняється. Linux запитує дані інтерактивно; Mac імпортує chiaki-ng. Не публікуйте ключі чи PIN.

## Керування та якість

Почніть із 720p; за нестабільного Wi-Fi зменште бітрейт або виберіть 30 FPS. На Android короткий рух угору від нижнього краю показує PS/Touch. На Linux Home — PS, Capture — тачпад. Перевірте звук, стики, курки та кнопки. Збережіть гру перед від’єднанням: трансляція не закриває гру.

## Оновлення

Android перевіряє GitHub за відкритої програми, зазвичай раз на шість годин, і може завантажувати через Wi-Fi. Android може вимагати підтвердження встановлення. Mac/Linux перевіряють підпис і хеш та чекають завершення трансляції. Не видаляйте програму чи дані. Старим приватним збіркам потрібен одноразовий перехід.

[Update details](../UPDATES.md)

## Помилки й обмеження

За помилки перевірте IP, профіль, Account ID, свіжий PIN та ізоляцію мережі. За чорного екрана закрийте інші клієнти й під’єднайтеся знову. Точні перевірені версії наведено нижче. Інтернет/VPN, довгі сеанси та всі контролери не перевірені. Windows, Intel Mac і Linux x64 заплановані. Deckivo не виправляє WebKit PS5.

[Device / version / scope](../TESTED.md) · [Technical reference (English)](../TECHNICAL.md)

## Підтримка

Добровільний донат через Ko-fi RemTeh підтримує відкриту розробку. Платних функцій та обіцянок індивідуальної допомоги немає.

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

---

Developed by [RemTeh.by](https://remteh.by/). [Chiaki / chiaki-ng / Android Extended](../../ATTRIBUTION.md). [AGPL v3 + OpenSSL permission](../../COPYING).
