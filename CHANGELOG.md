# 0.8.3 · controller safeguards and audit corrections · 2026-10-26

## 0.8.6 — 2026-10-26 (preview)

- Desktop: prevent Home title clipping in short MacBook windows. Reserve the measured title height, fit its font to the text column, and allow vertical scrolling when content needs more space.
- Console photography has a separate layout column; status, subtitle and console name wrap inside the text area.
- Same shared fix in the Ubuntu package. Android code 31 only aligns the release identity; no Android streaming changes. Desktop build 22.
- Fresh real-window captures and signed public update packages. Device checks remain explicit.

## 0.8.5 — 2026-10-26 (preview)

- Corrected the shared Sessions subtitle in English and Russian: history stays on this device, without incorrectly calling a Mac a Switch. Updated the legacy design exporter too.
- Android build 30; macOS and Ubuntu build 21. No pairing, session storage, streaming or controller behavior changes.


## 0.8.4 — 2026-10-26 (preview)

- Android build 29; macOS and Ubuntu build 20. Existing application IDs and signing identities retained.
- PS5 offline guidance, session-scoped donation reminders, readable Controller Lab reports and calibration-backup safeguards from the independent 0.8.3 audit.
- Optional download statistics no longer block Pages or the desktop update feed. Mobile buttons, localized copy and install/update/uninstall guidance improved.
- RU installation wording corrected; EN/RU instructions explain damaged calibration-backup reset, lab-only data scope and the required first-backup controller power cycle.
- Fresh real 0.8.4 desktop capture. Physical Switch, controller and PS5 session checks remain separate from automated release validation.


- Controller firmware tools compare version numbers only; binary firmware
  downloads and proxying are removed. Use Sony's official update method.
- Permanent controller writes require the default-off Service mode, a durable
  original-parameter backup and explicit confirmation with a mandatory checkbox.
  No permanent calibration was performed on real hardware for this release.
- Expanded English controller diagnostics, with automated deep-state Cyrillic
  checks and honest English fallback for the other 14 languages.
- Hide unknown funding progress and small download totals; preserve generated
  download-history documentation, one application schema and a real UI JPEG cover.
- Linux checks updates 45 seconds after login and then hourly with up to ten
  minutes of jitter; upgrades migrate the installed timer units.
- Android #28 and desktop b19 retain their existing identities. Switch lag
  diagnosis and sustained gameplay are not verified while the device is unavailable.

See [EN/RU release notes](docs/releases/0.8.3.md).

# 0.8.2 · project links and clearer downloads · 2026-10-25

- Fix a macOS/Ubuntu crash when clicking the donation link and preserve the
  support reminder choices; a failed browser launch keeps the QR fallback open.
- Visible GitHub and RemTeh.by links in Android, macOS and Ubuntu clients.
- RemTeh links identify Android, macOS, Ubuntu, GitHub or the Deckivo website
  using source-specific UTM parameters when the user opens a link.
- Simpler device-based download choices and constrained responsive layouts on
  the public website; genuine current-version application imagery is retained.
- Desktop build 18 and Android build 27 retain existing registrations and update
  identities. Android device acceptance remains separate from build checks.

# 0.8.1 · Linux updater fix · 2026-10-25

- Linux build 17 fixes the missing installed upgrade helper in clean 0.6.1
  installations, and adds signed background update staging through a systemd
  user timer. Installation still waits until Deckivo is open and idle.
- Immutable, hash-addressed update caches and a shared lock protect concurrent
  GUI/background checks; staged packages survive temporary network failures.
- Includes the shared controller lab and keyboard/mouse settings developed in
  0.7/0.8. Their full hardware matrix is not certified by updater tests.
- This release contains only the Switchroot Ubuntu ARM64 upgrade and source;
  published Android and macOS packages remain at 0.6.1.

See [release notes](docs/releases/0.8.1.md).

# 0.6.1 · 2026-10-25

Shared support/QR and bounded thank-you policy; offline licenses; Android updater localization and Lint corrections; strict pure-Python RSA verification; native 120-second startup rollback; static 16-language site, own UI imagery and release SBOMs. See [release notes](docs/releases/0.6.1.md).

# 0.6.0 · experimental public preview · 2026-10-25

- New GitHub presentation and responsive graphite/lime website, using the real
  PS5 photo, 16 language guides and exact device/build evidence.
- Visible Ko-fi RemTeh support links in Android, desktop, website and GitHub.
- Public GitHub/Pages update delivery, pinned native update signatures and
  constrained GitHub download redirects. macOS uses its native certificate store.
- Self-contained frozen Mac helper entry points and local chiaki-ng pairing import.
- Interactive Linux pairing; runtime and registration are retained on upgrades.
- Retains the physically verified 0.5.1 updater fixes: Android self-installation,
  safe Qt thread shutdown, desktop restart acknowledgment and rollback.
- Not certified: sustained Internet play, all controller functions, Windows,
  Intel Mac, Linux x64 or every redesigned frontend feature.

# История изменений

## 0.5.1 — 2026-10-25, частная проверка

- Подписанный канал обновлений для Mac, Android ARM64 и Switchroot Ubuntu ARM64.
- На Mac исправлен выход с работающим QThread; собран полноценный app bundle.
- Проверка номера установленной сборки исключает повтор одинакового обновления.
- Установка откладывается на время Remote Play; регистрации и настройки сохраняются.
- На Android добавлена штатная установка обновления самого приложения через
  PackageInstaller, с системным подтверждением при необходимости.
- На Mac проверены переходы 3 → 4 → 5, на физическом Switch Ubuntu — 6 → 7.
  Фактический Android-переход проверяется отдельно от сборки APK.
- Частный канал пока требует включённый Mac в общей локальной сети.

Перед этой проверкой подготовлен общий дизайн 0.5.0 для трёх платформ. Публичных
релизов нет; публикация остаётся отложенной до 1.0.0 и приёмки владельцем.

## 0.2.2 — 2026-10-24

Локальный кандидат Android versionCode 14. Исправлено дублирование сохранённой и найденной по сети консоли.

- Объединённая карточка показывает статус обнаруженной консоли и сохраняет связь с ручным адресом для редактирования и удаления закладки.
- Если поиск отключён или консоль не отвечает на обнаружение, сохранённая карточка остаётся доступна.
- Разные аппаратные идентификаторы и отдельные профили регистрации не объединяются в одну запись; база данных не изменяется.
- Добавлены восемь проверок объединения, включая одинаковые имена, повторно выданный IP, несколько ответов обнаружения и отдельный пользовательский профиль.

Публикация ждёт завершённой 1.0.0 и приёмки владельцем. Исправление переподключения из 0.2.1 сохранено.

## 0.2.1 — 2026-10-24

Локальный кандидат Android versionCode 13, исправление возобновления трансляции после переподключения. Публикация по-прежнему ждёт завершённой 1.0.0 и приёмки владельцем.

- Сеанс сохраняет действующую поверхность видеовывода между остановкой и переподключением; очищает её обработчик уничтожения поверхности.
- Новый декодер получает поверхность до запуска входящего видеопотока.
- Старый сеанс отвязывает обработчики перед остановкой и освобождением; ошибка запуска освобождает созданный сеанс.
- При уничтожении StreamViewModel освобождается действующий сеанс вместо неиспользуемого поля.

Проверки и фактическая приёмка описаны в `docs/releases/0.2.1-validation.json`.

## 0.2.0 — 2026-10-24

Deckivo — новое название RemTeh Remote Play. Локальная тестовая сборка Android versionCode 12. Сборки 4 и 5 оставлены внутренними; обнаруженный на устройстве HTTP 415 исправлен в сборке 6. Новый дизайн и языки подготовлены в сборке 7. Публикация новых версий и сайта — после завершённой 1.0.0 и приёмки владельцем.

- Название Deckivo и кликабельная подпись Developed by RemTeh.by; отдельное указание авторов Chiaki и лицензий.
- Раздел обновлений: автоматическая проверка при открытии раз в 6 часов, загрузка по Wi-Fi, выбор предварительных версий, ручная проверка и установка через Android.
- Проверка принадлежности релиза, HTTPS, размера, SHA-256, package/version/minSdk и сертификата APK. Установка подтверждается пользователем; регистрация PS5 сохраняется.
- Загрузка отменяется при уходе с главного экрана или экрана обновлений. Нет постоянного фонового сервиса и рекламы поверх игры.
- Полностью новый интерфейс Deckivo, карточки консолей, разделы настроек и скрытая панель трансляции.
- English по умолчанию, 16 языков, видимый переключатель и RTL для арабского. В сборке 8 добавлен режим «Автоматически» по языкам системы с английским как резервным; в сборке 9 исправлено раннее применение языка на Android 13+ и обновление подписи переключателя. Сборка 10 применяет выбранный язык ещё до отрисовки первого экрана и показывает правильный язык системы рядом с пунктом «Автоматически». Сборка 11 обновляет локализованный экран при выборе языка и после возвращения из системных настроек. В сборке 12 переключатель языка сохранён и на панели настроек после создания меню Android.
- Добровольная поддержка разработки без клиентских заявок, UTM, рекламы и платной техподдержки. Оплата пока не подключена.
- Локальный многоязычный сайт и план развития Android / Windows / macOS / Linux.
- Компилятор удаляет пути компьютера сборки из нативной библиотеки.

Помощник PS5 не изменён (0.1.0). Доступ через интернет и проблема reconnect после ошибки остаются отдельными задачами. Фактическая проверка устройства и обновления отражается в приложенных validation.json и acceptance.json, если последний опубликован после выпуска.

## 0.1.2 — 2026-10-24

Первый публичный предварительный выпуск, Android versionCode 3.

- PS и Touch перенесены в скрываемую нижнюю панель; постоянные белые кнопки поверх изображения убраны.
- Панель открывается жестом от нижнего края, исчезает после бездействия и остаётся видимой при удержании PS.
- Состояние кнопок сбрасывается при скрытии панели и уходе из приложения.
- На Switch OLED проверены установка поверх 0.1.1, сохранение регистрации, изображение, короткое и длинное нажатие PS.

APK совпадает с проверенной локальной сборкой. Публичное оформление, обезличенная документация и лицензии добавлены без пересборки приложения.

## 0.1.1 — 2026-10-24

Внутренняя сборка, Android versionCode 2.

- Исправлены два имени классов CoordinatorLayout, которые после смены applicationId приводили к падению интерфейса.
- Проверена первая привязка PS5 и локальная передача изображения, звука и базового управления на Switch OLED / Android 15 с GameSir G8+.

## 0.1.0 — 2026-10-24

Внутренняя начальная сборка, Android versionCode 1.

- Форк Chiaki / chiaki-ng Android Extended: собственный пакет, мастер локальной настройки, помощник PS5, профиль Switch OLED и настройка кнопок.
- Исправление завершения нативного декодера, исходники и стендовые тесты.
- На физическом устройстве найден дефект запуска интерфейса, исправленный в 0.1.1.

Помощник PS5 во всех этих выпусках остаётся версии 0.1.0.
