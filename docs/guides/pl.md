# Deckivo — instalacja i granie

Deckivo **0.6.0 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Zanim zaczniesz

Wersja 0.6.0 jest eksperymentalna. Połącz PS5 i klienta z tą samą siecią domową. Na PS5 wybierz właściwy profil i Ustawienia → System → Gra zdalna → Włącz grę zdalną. Konsola musi być włączona przy pierwszym parowaniu. Zalecane Wi-Fi 5 GHz; sieć gościnna może izolować urządzenia.

## Android

Pobierz APK arm64 z wydania. Wymagany Android 8+; testowano Switch OLED z Androidem 15. Zezwól na instalację tylko wybranemu źródłu. Instaluj na poprzedniej wersji bez usuwania danych. Wybierz język, kreator połączenia i sparuj kontroler Bluetooth w Androidzie. Nie wyłączaj Play Protect.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-0.6.0-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.6.0)

<a id="macos"></a>

## macOS

Tylko Apple Silicon. Zainstaluj osobno chiaki-ng, zarejestruj PS5 i zamknij jego transmisję. Rozpakuj ZIP i przenieś Deckivo.app do ~/Applications. Brak notaryzacji: macOS może wymagać „Otwórz mimo to” w ustawieniach prywatności i bezpieczeństwa. Nie wyłączaj Gatekeepera. Zaimportuj rejestrację chiaki-ng w Deckivo i podaj IP konsoli.

[Mac ZIP · 0.6.0 b9](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-macos-0.6.0-b9.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Podgląd deweloperski: Switchroot Ubuntu 24.04 ARM64, KDE/X11 i FFmpeg 6.1. Pierwsza instalacja wymaga pełnych źródeł, PyQt5, GCC i zależności. Uruchom polecenia poniżej. Mały ZIP służy wyłącznie do aktualizacji istniejącego runtime. Nie zastępuj sterowników.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux technical requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-0.6.0-sources.zip)

## Parowanie

Potrzebny jest Account ID właściwego profilu w Base64, a nie pseudonim czy e-mail. Na PS5 otwórz Gra zdalna → Połącz urządzenie i wpisz nowy ośmiocyfrowy kod przed końcem czasu. Kod opcjonalnego pomocnika ELF jest inny. Linux pyta interaktywnie; Mac importuje chiaki-ng. Nie publikuj kluczy ani PIN-u.

## Sterowanie i jakość

Zacznij od 720p; przy problemach zmniejsz bitrate lub wybierz 30 FPS. Android: przesuń od dolnej krawędzi w górę, aby wyświetlić PS/Touch. Linux: Home to PS, Capture to touchpad. Sprawdź dźwięk, drążki, spusty i przyciski. Zapisz grę przed rozłączeniem; zakończenie transmisji nie zamyka gry.

## Aktualizacje

Android sprawdza GitHub przy otwartej aplikacji, zwykle co sześć godzin; może pobierać przez nielimitowane Wi-Fi. System może zażądać potwierdzenia instalacji. Mac/Linux sprawdzają podpis i hash, czekają na koniec transmisji i restartują aplikację. Zachowaj dane. Stare kompilacje prywatne wymagają jednorazowej migracji.

[Update details](../UPDATES.md)

## Problemy i ograniczenia

Przy błędzie sprawdź IP, profil, Account ID, nowy PIN i izolację sieci. Czarny ekran: zamknij inne klienty i połącz ponownie. Dokładne testy wersji są poniżej. Internet/VPN, długie sesje i wszystkie funkcje kontrolerów nie są potwierdzone. Windows, Intel Mac i Linux x64 są planowane. Deckivo nie naprawia WebKit na PS5.

[Device / version / scope](../TESTED.md) · [Technical reference (English)](../TECHNICAL.md)

## Wsparcie

Dobrowolny Ko-fi RemTeh wspiera rozwój. Brak płatnych funkcji i obietnic indywidualnej konfiguracji.

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

---

Developed by [RemTeh.by](https://remteh.by/). [Chiaki / chiaki-ng / Android Extended](../../ATTRIBUTION.md). [AGPL v3 + OpenSSL permission](../../COPYING).
