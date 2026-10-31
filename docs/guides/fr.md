# Deckivo — installation et jeu

Deckivo **0.8.8 preview** · 2026-11-01

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Avant de commencer

La version 0.8.8 est expérimentale. Connectez la PS5 et le client au même réseau domestique. Sur PS5, choisissez le bon profil puis Paramètres → Système → Lecture à distance → Activer. Laissez la console allumée pendant la première association. Préférez le Wi-Fi 5 GHz ; un réseau invité peut isoler les appareils.

<a id="android"></a>

## Android

Téléchargez l’APK arm64 du release. Android 8+ requis ; tests physiques sur Switch OLED avec Android 15. Autorisez uniquement la source choisie. Installez par-dessus l’ancienne version sans supprimer ses données. Choisissez la langue, l’assistant de connexion et associez la manette Bluetooth dans Android. Ne désactivez pas Play Protect.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.8/Deckivo-0.8.8-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.8)

<a id="macos"></a>

## macOS

Apple Silicon uniquement. Installez chiaki-ng séparément, enregistrez la PS5 et fermez son flux. Décompressez le ZIP Mac et placez Deckivo.app dans ~/Applications. Application non notariée : macOS peut demander « Ouvrir quand même » dans Confidentialité et sécurité. Ne désactivez pas Gatekeeper. Importez l’enregistrement chiaki-ng dans Deckivo et renseignez l’IP.

[Mac ZIP · 0.8.8 b24](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.8/Deckivo-macos-0.8.8-b24.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Aperçu développeur pour Switchroot Ubuntu 24.04 ARM64, KDE/X11 et FFmpeg 6.1. La première installation nécessite les sources complètes, PyQt5, GCC et les dépendances. Utilisez les commandes ci-dessous. Le petit ZIP ne met à jour qu’un runtime existant. Ne remplacez pas les pilotes NVIDIA/FFmpeg.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux update ZIP · 0.8.8 b24](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.8/Deckivo-Linux-0.8.8-b24-source.zip) · [Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.8/Deckivo-0.8.8-sources.zip)

## Associer la console

Utilisez l’Account ID Base64 du bon profil, pas son pseudo ni son adresse mail. Sur PS5, ouvrez Lecture à distance → Associer un périphérique et saisissez le nouveau code à huit chiffres avant expiration. Le code de l’assistant ELF est différent. Linux demande les données de façon interactive ; Mac importe chiaki-ng. Ne publiez jamais clés ou codes.

## Commandes et qualité

Commencez en 720p ; réduisez le débit ou passez à 30 FPS si nécessaire. Android : balayez brièvement depuis le bord inférieur pour afficher PS/Touch. Linux : Home correspond à PS, Capture au pavé tactile. Vérifiez son, sticks, gâchettes et boutons. Sauvegardez avant de quitter : couper le flux ne ferme pas le jeu.

## Mises à jour

Android consulte GitHub avec l’application ouverte, généralement toutes les six heures, et peut télécharger sur Wi-Fi non limité. Le système peut demander une confirmation. Mac/Linux vérifient signature et empreinte, puis attendent la fin du flux. Conservez les données. Les anciennes versions privées nécessitent une migration unique.

[Update details](../UPDATES.md)

## Dépannage et limites

En cas d’échec, vérifiez IP, profil, Account ID, nouveau code et isolation réseau. Écran noir : fermez les autres clients et reconnectez-vous. Consultez la matrice exacte ci-dessous. Internet/VPN, longues sessions et toutes les fonctions des manettes ne sont pas certifiés. Windows, Intel Mac et Linux x64 sont prévus. Deckivo ne répare pas WebKit sur PS5.

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## Aidez Deckivo à grandir

Deckivo est gratuit et open source. Votre soutien finance les plateformes et les tests sur appareils.

- Apple Developer ID ($99/yr) — signature et notarisation Mac
- Version Windows
- Plus de matériel : PS5 Pro et consoles portables

- [Ko-fi · RemTeh](https://ko-fi.com/pavelzayats) — Soutien ponctuel ou mensuel. Page configurée.
- [Patreon](https://www.patreon.com/c/deckivo) — Soutien mensuel. Réception des paiements non testée.
- [Afdian · 爱发电](https://afdian.com/a/deckivo) — Soutien mensuel. Validation du profil en attente.
- [Boosty](https://boosty.to/remteh) — Page du créateur. En cours de préparation.
- [DonationAlerts](https://www.donationalerts.com/r/deckivo) — Soutien ponctuel. Réception des paiements non testée.
- [DonatePay](https://donatepay.ru/don/1541009) — Soutien ponctuel. Réception des paiements non testée.
- [OKX Pay](https://okx.com/ul/VQfh84m) — Transfert dans l’application OKX. Réception des paiements non testée.

Les paiements sont traités par le service choisi. Vérifiez le statut et les options de paiement avant de continuer.

<details>
<summary>Scannez avec votre téléphone</summary>

Ko-fi · RemTeh
<img src="../../website/assets/support/kofi.svg?v=dc1c37f9125b" width="180" height="180" alt="Scannez avec votre téléphone">

Patreon
<img src="../../website/assets/support/patreon.svg?v=f9e58ec6f1d9" width="180" height="180" alt="Scannez avec votre téléphone">

Afdian · 爱发电
<img src="../../website/assets/support/afdian.svg?v=8d31fd917144" width="180" height="180" alt="Scannez avec votre téléphone">

Boosty
<img src="../../website/assets/support/boosty.svg?v=7c00bd5f2a9a" width="180" height="180" alt="Scannez avec votre téléphone">

DonationAlerts
<img src="../../website/assets/support/donationalerts.svg?v=c45161fae4e6" width="180" height="180" alt="Scannez avec votre téléphone">

DonatePay
<img src="../../website/assets/support/donatepay.svg?v=6c0beed9ff84" width="180" height="180" alt="Scannez avec votre téléphone">

OKX Pay
<img src="../../website/assets/support/okx_pay.svg?v=2b6a3d8c1a9b" width="180" height="180" alt="Scannez avec votre téléphone">

</details>

Tout reste gratuit. Le soutien est facultatif.
<!-- SUPPORT:END -->
