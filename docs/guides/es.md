# Deckivo — instalación y juego

Deckivo **0.6.0 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Antes de empezar

0.6.0 es una versión experimental. Conecta PS5 y cliente a la misma red doméstica. En PS5 selecciona el perfil correcto: Ajustes → Sistema → Uso a distancia → Activar. Mantén la consola encendida durante la primera vinculación. Es preferible Wi-Fi de 5 GHz; la red de invitados puede aislar dispositivos.

## Android

Descarga el APK arm64 del lanzamiento. Requiere Android 8+; probado físicamente en Switch OLED con Android 15. Autoriza solo la fuente elegida. Instala sobre Deckivo anterior sin borrar datos. Elige idioma, asistente de conexión y empareja el mando Bluetooth en Android. No desactives Play Protect.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-0.6.0-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.6.0)

<a id="macos"></a>

## macOS

Solo Apple Silicon. Instala chiaki-ng por separado, registra PS5 y cierra su transmisión. Extrae el ZIP Mac y mueve Deckivo.app a ~/Applications. No está notarizada: macOS puede pedir «Abrir igualmente» en Privacidad y seguridad. No desactives Gatekeeper globalmente. Importa el registro de chiaki-ng en Deckivo e introduce la IP.

[Mac ZIP · 0.6.0 b9](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-macos-0.6.0-b9.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Vista previa para desarrolladores: Switchroot Ubuntu 24.04 ARM64, KDE/X11 y FFmpeg 6.1. La instalación inicial necesita fuentes completas, PyQt5, GCC y dependencias. Usa los comandos inferiores. El ZIP pequeño solo actualiza un runtime existente. No sustituyas controladores NVIDIA/FFmpeg.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux technical requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-0.6.0-sources.zip)

## Vincular la consola

Usa el Account ID Base64 del perfil correcto, no apodo ni correo. En PS5 abre Uso a distancia → Vincular dispositivo e introduce el nuevo código de ocho cifras antes de que caduque. El código del ayudante ELF es distinto. Linux solicita los datos de forma interactiva; Mac importa chiaki-ng. No publiques claves ni PIN.

## Controles y calidad

Empieza con 720p; reduce bitrate o usa 30 FPS si la red falla. Android: desliza brevemente desde el borde inferior para mostrar PS/Touch. Linux: Home es PS y Capture es panel táctil. Comprueba audio, palancas, gatillos y botones. Guarda antes de desconectar: cerrar la transmisión no cierra el juego.

## Actualizaciones

Android consulta GitHub con la app abierta, normalmente cada seis horas, y puede descargar con Wi-Fi sin límite. El sistema puede pedir confirmación. Mac/Linux verifican firma y hash y esperan a que termine la transmisión. Conserva datos. Las versiones privadas antiguas requieren una migración única.

[Update details](../UPDATES.md)

## Problemas y límites

Si falla, comprueba IP, perfil, Account ID, código nuevo y aislamiento de red. Pantalla negra: cierra otros clientes y reconecta. Consulta las versiones probadas abajo. Internet/VPN, sesiones largas y todas las funciones del mando no están certificados. Windows, Intel Mac y Linux x64 están previstos. Deckivo no repara WebKit de PS5.

[Device / version / scope](../TESTED.md) · [Technical reference (English)](../TECHNICAL.md)

## Apoyar el proyecto

Ko-fi RemTeh permite apoyar voluntariamente el desarrollo. No hay funciones de pago ni promesa de asistencia individual.

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

---

Developed by [RemTeh.by](https://remteh.by/). [Chiaki / chiaki-ng / Android Extended](../../ATTRIBUTION.md). [AGPL v3 + OpenSSL permission](../../COPYING).
