# Deckivo — panduan instalasi dan bermain

Deckivo **0.8.6 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## Sebelum mulai

0.8.6 adalah pratinjau eksperimental. Hubungkan PS5 dan klien ke jaringan rumah yang sama. Pilih profil yang benar di PS5: Pengaturan → Sistem → Remote Play → Aktifkan. Biarkan konsol menyala saat pemasangan pertama. Wi-Fi 5 GHz disarankan; jaringan tamu dapat mengisolasi perangkat.

<a id="android"></a>

## Android

Unduh APK arm64 dari rilis. Memerlukan Android 8+; pengujian fisik memakai Switch OLED dengan Android 15. Izinkan instalasi hanya dari sumber yang dipilih. Pasang di atas versi lama tanpa menghapus aplikasi atau data. Pilih bahasa dan panduan koneksi, lalu pasangkan kontroler Bluetooth di Android. Jangan matikan Play Protect.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.6/Deckivo-0.8.6-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.6)

<a id="macos"></a>

## macOS

Hanya Apple Silicon. Instal chiaki-ng secara terpisah, daftarkan PS5 dan tutup streaming-nya. Ekstrak ZIP Mac dan pindahkan Deckivo.app ke ~/Applications. Belum dinotarisasi: macOS dapat meminta “Open Anyway” di Privasi & Keamanan. Jangan matikan Gatekeeper secara global. Impor pendaftaran chiaki-ng dalam Deckivo dan masukkan IP konsol.

[Mac ZIP · 0.8.6 b22](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.6/Deckivo-macos-0.8.6-b22.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Pratinjau pengembang untuk Switchroot Ubuntu 24.04 ARM64, KDE/X11 dan FFmpeg 6.1. Instalasi awal memerlukan sumber lengkap, PyQt5, GCC dan dependensi. Jalankan perintah di bawah dari akar sumber, lalu pemasangan interaktif. ZIP kecil hanya memperbarui runtime yang sudah ada. Jangan mengganti driver NVIDIA/FFmpeg.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux update ZIP · 0.8.6 b22](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.6/Deckivo-Linux-0.8.6-b22-source.zip) · [Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.6/Deckivo-0.8.6-sources.zip)

## Memasangkan konsol

Gunakan Account ID Base64 milik profil yang benar, bukan nama panggilan atau email. Buka Remote Play → Tautkan Perangkat di PS5 dan masukkan kode baru delapan digit sebelum habis. Kode pembantu ELF opsional berbeda. Linux meminta data secara interaktif; Mac mengimpor chiaki-ng. Jangan publikasikan PIN, kunci atau berkas pendaftaran.

## Kontrol dan kualitas

Mulai dengan 720p; kurangi bitrate atau pilih 30 FPS jika jaringan tidak stabil. Android: usap singkat ke atas dari tepi bawah untuk PS/Touch. Linux: Home adalah PS, Capture adalah touchpad. Periksa suara, stik, pemicu dan tombol. Simpan permainan sebelum memutus koneksi; menutup streaming tidak menutup gim.

## Pembaruan otomatis

Android memeriksa GitHub saat layar utama/pembaruan terbuka, biasanya setiap enam jam, dan dapat mengunduh di Wi-Fi tanpa batas. Sistem mungkin meminta konfirmasi. Mac/Linux memeriksa tanda tangan dan hash serta menunggu streaming selesai. Pertahankan data. Build pribadi lama memerlukan migrasi sekali.

[Update details](../UPDATES.md)

## Masalah dan batasan

Jika gagal, periksa IP, profil, Account ID, PIN baru dan isolasi jaringan. Layar hitam: tutup klien lain lalu sambungkan ulang. Versi pengujian tepat ada di bawah. Internet/VPN, bangun dari tidur, sesi panjang dan semua fungsi kontroler belum tersertifikasi. Windows, Intel Mac dan Linux x64 direncanakan. Deckivo tidak memperbaiki WebKit PS5.

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## Bantu Deckivo berkembang

Deckivo gratis dan terbuka. Dukungan membantu platform baru dan pengujian perangkat nyata.

- Apple Developer ID ($99/yr) — tanda tangan dan notarisasi Mac
- Versi Windows
- Perangkat tambahan: PS5 Pro dan handheld

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="Pindai dengan ponsel">

Semuanya tetap gratis. Dukungan opsional.
<!-- SUPPORT:END -->
