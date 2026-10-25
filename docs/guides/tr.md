# Deckivo — kurulum ve oyun kılavuzu

Deckivo **0.6.0 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Başlamadan önce

0.6.0 deneysel bir ön sürümdür. PS5 ile istemciyi aynı ev ağına bağlayın. PS5’te doğru profili seçin: Ayarlar → Sistem → Uzaktan Oynama → Etkinleştir. İlk eşleştirmede konsolu açık tutun. 5 GHz Wi-Fi önerilir; misafir ağı cihazları birbirinden ayırabilir.

## Android

Sürümden arm64 APK dosyasını indirin. Android 8+ gerekir; fiziksel test Switch OLED ve Android 15 üzerinde yapıldı. Yalnızca seçtiğiniz kaynağa kurulum izni verin. Uygulamayı kaldırmadan ve verileri silmeden eski sürümün üzerine kurun. Dil ve bağlantı sihirbazını seçin, Bluetooth kontrolcüsünü Android’de eşleştirin. Play Protect’i kapatmayın.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-0.6.0-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.6.0)

<a id="macos"></a>

## macOS

Yalnızca Apple Silicon. chiaki-ng’yi ayrıca kurup PS5’i kaydedin ve yayınını kapatın. Mac ZIP dosyasını açıp Deckivo.app’i ~/Applications içine taşıyın. Noter onayı yoktur; macOS Gizlilik ve Güvenlik bölümünde «Yine de Aç» isteyebilir. Gatekeeper’ı tamamen kapatmayın. Deckivo’da chiaki-ng kaydını içe aktarıp konsol IP’sini girin.

[Mac ZIP · 0.6.0 b9](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-macos-0.6.0-b9.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Geliştirici ön sürümü Switchroot Ubuntu 24.04 ARM64, KDE/X11 ve FFmpeg 6.1 içindir. İlk kurulum tam kaynak, PyQt5, GCC ve bağımlılıklar gerektirir. Aşağıdaki komutları kullanın. Küçük ZIP yalnızca mevcut çalışma ortamını günceller. NVIDIA/FFmpeg sürücülerini değiştirmeyin.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux technical requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.0/Deckivo-0.6.0-sources.zip)

## Konsolu eşleştirme

Doğru profilin Base64 Account ID değerini kullanın; takma ad veya e-posta değildir. PS5 Uzaktan Oynama → Cihaz Bağla ekranındaki yeni sekiz haneli kodu süresi dolmadan girin. İsteğe bağlı ELF yardımcısının kodu farklıdır. Linux bilgileri etkileşimli sorar; Mac chiaki-ng’den aktarır. Anahtar veya PIN yayımlamayın.

## Kontroller ve kalite

720p ile başlayın; kararsız ağda bit hızını azaltın veya 30 FPS seçin. Android’de alt kenardan kısa bir yukarı kaydırma PS/Touch düğmelerini gösterir. Linux’ta Home PS, Capture dokunmatik yüzeydir. Ses, çubuklar, tetikler ve düğmeleri sınayın. Bağlantıyı kesmeden kaydedin; yayın kapanınca oyun kapanmaz.

## Güncellemeler

Android uygulama açıkken GitHub’ı genellikle altı saatte bir denetler ve sınırsız Wi-Fi üzerinden indirebilir. Sistem kurulum onayı isteyebilir. Mac/Linux imzayı ve özeti doğrular, yayının bitmesini bekler. Verileri koruyun. Eski özel sürümler tek seferlik geçiş gerektirir.

[Update details](../UPDATES.md)

## Sorunlar ve sınırlar

Hatada IP, profil, Account ID, yeni PIN ve ağ yalıtımını kontrol edin. Siyah ekranda diğer istemcileri kapatıp yeniden bağlanın. Kesin sürümler aşağıdadır. İnternet/VPN, uzun oturumlar ve tüm kontrolcü işlevleri doğrulanmadı. Windows, Intel Mac ve Linux x64 planlanıyor. Deckivo PS5 WebKit’i onarmaz.

[Device / version / scope](../TESTED.md) · [Technical reference (English)](../TECHNICAL.md)

## Projeyi destekleyin

Ko-fi RemTeh desteği isteğe bağlıdır. Ücretli özellik veya kişisel kurulum hizmeti sözü verilmez.

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

---

Developed by [RemTeh.by](https://remteh.by/). [Chiaki / chiaki-ng / Android Extended](../../ATTRIBUTION.md). [AGPL v3 + OpenSSL permission](../../COPYING).
