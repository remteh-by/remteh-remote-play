# Deckivo — installazione e gioco

Deckivo **0.7.0 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Prima di iniziare

0.6.1 è un’anteprima sperimentale. Collega PS5 e client alla stessa rete domestica. Su PS5 scegli il profilo corretto: Impostazioni → Sistema → Riproduzione remota → Abilita. Mantieni la console accesa per la prima associazione. Preferisci Wi-Fi 5 GHz; le reti ospiti possono isolare i dispositivi.

## Android

Scarica l’APK arm64 dal rilascio. Richiede Android 8+; test fisici su Switch OLED con Android 15. Autorizza soltanto la sorgente scelta. Installa sopra la vecchia versione senza cancellare dati. Seleziona lingua e procedura di connessione; associa il controller Bluetooth in Android. Non disattivare Play Protect.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.7.0/Deckivo-0.7.0-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.7.0)

<a id="macos"></a>

## macOS

Solo Apple Silicon. Installa chiaki-ng separatamente, registra PS5 e chiudi il suo flusso. Estrai lo ZIP Mac e sposta Deckivo.app in ~/Applications. App non notarizzata: macOS può richiedere «Apri comunque» in Privacy e sicurezza. Non disattivare Gatekeeper. Importa la registrazione chiaki-ng in Deckivo e inserisci l’IP.

[Mac ZIP · 0.7.0 b11](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.7.0/Deckivo-macos-0.7.0-b11.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Anteprima sviluppatori per Switchroot Ubuntu 24.04 ARM64, KDE/X11 e FFmpeg 6.1. La prima installazione richiede sorgenti completi, PyQt5, GCC e dipendenze. Esegui i comandi seguenti. Lo ZIP piccolo aggiorna solo un runtime già presente. Non sostituire i driver NVIDIA/FFmpeg.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.7.0/Deckivo-0.7.0-sources.zip)

## Associazione

Usa l’Account ID Base64 del profilo corretto, non soprannome o email. Su PS5 apri Riproduzione remota → Collega dispositivo e inserisci un nuovo codice di otto cifre prima della scadenza. Il codice dell’assistente ELF è diverso. Linux richiede i dati interattivamente; Mac importa chiaki-ng. Non pubblicare chiavi o PIN.

## Comandi e qualità

Inizia a 720p; riduci bitrate o passa a 30 FPS con Wi-Fi instabile. Android: scorri brevemente dal bordo inferiore per PS/Touch. Linux: Home è PS, Capture è touchpad. Verifica audio, stick, grilletti e pulsanti. Salva prima di scollegarti: terminare il flusso non chiude il gioco.

## Aggiornamenti

Android controlla GitHub con l’app aperta, normalmente ogni sei ore, e può scaricare su Wi-Fi senza limiti. Il sistema può chiedere conferma. Mac/Linux verificano firma e hash e aspettano che il flusso termini. Conserva i dati. Le vecchie build private richiedono un passaggio iniziale.

[Update details](../UPDATES.md)

## Problemi e limiti

In caso di errore controlla IP, profilo, Account ID, nuovo PIN e isolamento di rete. Schermo nero: chiudi altri client e riconnetti. La matrice sotto riporta le versioni precise. Internet/VPN, sessioni lunghe e ogni funzione dei controller non sono certificati. Windows, Intel Mac e Linux x64 sono previsti. Deckivo non ripara WebKit PS5.

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## Aiuta Deckivo a crescere

Deckivo è gratuito e open source. Il sostegno aiuta nuove piattaforme e test reali.

- Apple Developer ID ($99/yr) — firma e notarizzazione Mac
- Versione Windows
- Più dispositivi: PS5 Pro e console portatili

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="Scansiona con il telefono">

Tutto resta gratuito. Il sostegno è facoltativo.
<!-- SUPPORT:END -->
