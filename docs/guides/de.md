# Deckivo — Installation und Spielen

Deckivo **0.8.3 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Vorbereitung

0.8.3 ist eine experimentelle Vorschau. Verbinde PS5 und Client mit demselben Heimnetz. Wähle auf der PS5 das gewünschte Profil und Einstellungen → System → Remote Play → Remote Play aktivieren. Bei der ersten Kopplung muss die Konsole eingeschaltet bleiben. 5-GHz-WLAN ist vorzuziehen; Gastnetze können Geräte isolieren.

<a id="android"></a>

## Android

Lade die arm64-APK aus dem Release. Android 8+ ist erforderlich; physisch getestet wurde Switch OLED mit Android 15. Erlaube die Installation nur der gewählten Quelle. Installiere über die vorhandene Version, ohne Daten zu löschen. Wähle Sprache und Verbindungsassistent; kopple den Bluetooth-Controller in Android. Play Protect nicht deaktivieren.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.3/Deckivo-0.8.3-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.3)

<a id="macos"></a>

## macOS

Nur Apple Silicon. Installiere chiaki-ng separat, registriere die PS5 und beende dessen Stream. Entpacke das Mac-ZIP und verschiebe Deckivo.app nach ~/Applications. Die App ist nicht notarisiert; macOS kann „Dennoch öffnen“ unter Datenschutz & Sicherheit verlangen. Gatekeeper nicht global deaktivieren. Importiere in Deckivo die chiaki-ng-Registrierung und gib die Konsolen-IP ein.

[Mac ZIP · 0.8.3 b19](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.3/Deckivo-macos-0.8.3-b19.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Entwicklervorschau für Switchroot Ubuntu 24.04 ARM64 mit KDE/X11 und FFmpeg 6.1. Eine Erstinstallation benötigt vollständige Quellen, PyQt5, GCC und Abhängigkeiten. Nutze die Befehle unten. Das kleine ZIP aktualisiert nur eine vorhandene Laufzeit. Keine NVIDIA-/FFmpeg-Treiber ersetzen.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux update ZIP · 0.8.3 b19](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.3/Deckivo-Linux-0.8.3-b19-source.zip) · [Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.3/Deckivo-0.8.3-sources.zip)

## Konsole koppeln

Verwende die Base64-Account-ID des richtigen Profils, nicht Spitzname oder E-Mail. Öffne auf der PS5 Remote Play → Gerät verknüpfen und gib den neuen achtstelligen Code rechtzeitig ein. Der optionale ELF-Helfer hat einen anderen Code. Linux fragt interaktiv; Mac importiert chiaki-ng. Schlüssel und PIN niemals veröffentlichen.

## Steuerung und Qualität

Beginne mit 720p; reduziere bei WLAN-Problemen Bitrate oder auf 30 FPS. Android: vom unteren Rand kurz nach oben wischen, um PS/Touch einzublenden. Linux: Home entspricht PS, Capture dem Touchpad. Prüfe Ton, Sticks, Trigger und Tasten. Vor dem Trennen speichern: Der Stream-Abbruch beendet nicht das Spiel.

## Updates

Android prüft GitHub bei geöffneter App normalerweise alle sechs Stunden und kann über ungetaktetes WLAN herunterladen. Android darf eine Bestätigung verlangen. Mac/Linux prüfen Signatur und Hash und warten auf einen inaktiven Stream. Einstellungen behalten, App nicht löschen. Alte private Builds benötigen einen einmaligen Wechsel.

[Update details](../UPDATES.md)

## Fehler und Grenzen

Bei Fehlern IP, Profil, Account-ID, frischen PIN und Netzisolation prüfen. Schwarzes Bild: andere Clients schließen und neu verbinden. Die genaue Versionsmatrix steht unten. Internet/VPN, lange Sitzungen und sämtliche Controllerfunktionen sind nicht bestätigt. Windows, Intel Mac und Linux x64 sind geplant. Deckivo repariert kein PS5-WebKit.

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## Hilf Deckivo zu wachsen

Deckivo ist kostenlos und quelloffen. Unterstützung hilft bei neuen Plattformen und Gerätetests.

- Apple Developer ID ($99/yr) — Signatur und Notarisierung für Mac
- Windows-Version
- Mehr Testgeräte: PS5 Pro und Handhelds

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="Mit dem Handy scannen">

Alles bleibt kostenlos. Unterstützung ist freiwillig.
<!-- SUPPORT:END -->
