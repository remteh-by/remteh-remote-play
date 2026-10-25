# Deckivo — instalação e jogo

Deckivo **0.7.0 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Antes de começar

0.6.1 é uma versão experimental. Ligue a PS5 e o cliente à mesma rede doméstica. Na PS5 escolha o perfil correto: Definições → Sistema → Reprodução remota → Ativar. Mantenha a consola ligada no primeiro emparelhamento. Prefira Wi-Fi de 5 GHz; redes de convidados podem isolar dispositivos.

## Android

Transfira o APK arm64 do lançamento. Requer Android 8+; testado fisicamente na Switch OLED com Android 15. Autorize apenas a origem escolhida. Instale sobre a versão anterior sem apagar dados. Escolha idioma, assistente de ligação e emparelhe o comando Bluetooth no Android. Não desative o Play Protect.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.7.0/Deckivo-0.7.0-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.7.0)

<a id="macos"></a>

## macOS

Apenas Apple Silicon. Instale chiaki-ng separadamente, registe a PS5 e feche a transmissão. Extraia o ZIP Mac e mova Deckivo.app para ~/Applications. Não tem notarização: o macOS pode pedir «Abrir mesmo assim» em Privacidade e segurança. Não desative o Gatekeeper. Importe o registo chiaki-ng no Deckivo e indique o IP.

[Mac ZIP · 0.7.0 b11](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.7.0/Deckivo-macos-0.7.0-b11.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Prévia para programadores: Switchroot Ubuntu 24.04 ARM64, KDE/X11 e FFmpeg 6.1. A primeira instalação exige código-fonte completo, PyQt5, GCC e dependências. Execute os comandos abaixo. O ZIP pequeno só atualiza um runtime existente. Não substitua os controladores NVIDIA/FFmpeg.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.7.0/Deckivo-0.7.0-sources.zip)

## Emparelhar a consola

Use o Account ID Base64 do perfil correto, não a alcunha nem o email. Na PS5 abra Reprodução remota → Associar dispositivo e introduza o novo código de oito dígitos antes de expirar. O código do auxiliar ELF é diferente. Linux pede os dados interativamente; Mac importa chiaki-ng. Não publique chaves nem PIN.

## Controlos e qualidade

Comece em 720p; reduza o bitrate ou escolha 30 FPS se a rede falhar. Android: deslize brevemente a partir da borda inferior para PS/Touch. Linux: Home é PS, Capture é touchpad. Teste som, analógicos, gatilhos e botões. Guarde o jogo antes de desligar: terminar a transmissão não fecha o jogo.

## Atualizações

Android verifica o GitHub com a aplicação aberta, normalmente de seis em seis horas, e pode descarregar em Wi-Fi sem limites. O sistema pode exigir confirmação. Mac/Linux verificam assinatura e hash e aguardam o fim da transmissão. Preserve os dados. Builds privadas antigas precisam de uma migração inicial.

[Update details](../UPDATES.md)

## Problemas e limites

Em caso de falha, verifique IP, perfil, Account ID, PIN novo e isolamento da rede. Ecrã preto: feche outros clientes e volte a ligar. Consulte as versões testadas abaixo. Internet/VPN, sessões longas e todas as funções de comandos não estão certificados. Windows, Intel Mac e Linux x64 estão planeados. Deckivo não corrige WebKit da PS5.

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## Ajuda o Deckivo a crescer

O Deckivo é gratuito e aberto. O apoio ajuda novas plataformas e testes reais.

- Apple Developer ID ($99/yr) — assinatura e notarização Mac
- Versão Windows
- Mais dispositivos: PS5 Pro e portáteis

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="Lê com o telemóvel">

Tudo continua gratuito. O apoio é opcional.
<!-- SUPPORT:END -->
