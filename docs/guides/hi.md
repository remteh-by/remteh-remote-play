# Deckivo — स्थापना और खेलने की मार्गदर्शिका

Deckivo **0.8.5 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## शुरू करने से पहले

0.8.5 प्रयोगात्मक संस्करण है। PS5 और क्लाइंट को एक ही घरेलू नेटवर्क से जोड़ें। PS5 पर सही प्रोफ़ाइल चुनें: सेटिंग्स → सिस्टम → रिमोट प्ले → सक्षम करें। पहली बार जोड़ते समय कंसोल चालू रखें। 5 GHz Wi-Fi बेहतर है; अतिथि नेटवर्क उपकरणों को अलग कर सकता है।

<a id="android"></a>

## Android

रिलीज़ से arm64 APK डाउनलोड करें। Android 8+ आवश्यक है; वास्तविक परीक्षण Switch OLED और Android 15 पर हुआ। केवल चुने हुए स्रोत को स्थापना की अनुमति दें। पुराना ऐप या डेटा हटाए बिना ऊपर से इंस्टॉल करें। भाषा और कनेक्शन विज़ार्ड चुनें तथा Android Bluetooth में गेमपैड जोड़ें। Play Protect बंद न करें।

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.5/Deckivo-0.8.5-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.8.5)

<a id="macos"></a>

## macOS

केवल Apple Silicon। आधिकारिक chiaki-ng अलग से इंस्टॉल करें, PS5 पंजीकृत करें और उसकी स्ट्रीम बंद करें। Mac ZIP खोलकर Deckivo.app को ~/Applications में रखें। ऐप notarized नहीं है; गोपनीयता और सुरक्षा में “Open Anyway” आवश्यक हो सकता है। Gatekeeper पूरी तरह बंद न करें। Deckivo में chiaki-ng पंजीकरण आयात करके कंसोल का IP भरें।

[Mac ZIP · 0.8.5 b21](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.5/Deckivo-macos-0.8.5-b21.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

Switchroot Ubuntu 24.04 ARM64, KDE/X11 और FFmpeg 6.1 के लिए डेवलपर प्रीव्यू। पहली स्थापना को पूरा स्रोत, PyQt5, GCC और निर्भरताएँ चाहिए। स्रोत के मूल फ़ोल्डर में नीचे के आदेश चलाएँ, फिर संवादात्मक पेयरिंग करें। छोटा ZIP केवल मौजूदा runtime अपडेट करता है। NVIDIA/FFmpeg ड्राइवर न बदलें।

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux update ZIP · 0.8.5 b21](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.5/Deckivo-Linux-0.8.5-b21-source.zip) · [Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.8.5/Deckivo-0.8.5-sources.zip)

## कंसोल जोड़ना

सही प्रोफ़ाइल की Base64 Account ID चाहिए, उपनाम या ईमेल नहीं। PS5 में रिमोट प्ले → डिवाइस लिंक करें खोलें और समय समाप्त होने से पहले नया आठ अंकों का कोड भरें। वैकल्पिक ELF सहायक का कोड अलग है। Linux संवादात्मक इनपुट लेता है; Mac chiaki-ng से आयात करता है। PIN, कुंजियाँ या पंजीकरण फ़ाइल साझा न करें।

## नियंत्रण और गुणवत्ता

720p से शुरू करें; अस्थिर नेटवर्क पर बिटरेट घटाएँ या 30 FPS चुनें। Android में नीचे के किनारे से थोड़ा ऊपर स्वाइप करने पर PS/Touch दिखता है। Linux में Home का अर्थ PS और Capture का अर्थ टचपैड है। ध्वनि, स्टिक, ट्रिगर और बटन जाँचें। डिस्कनेक्ट से पहले सेव करें; स्ट्रीम बंद करने से गेम बंद नहीं होता।

## स्वचालित अपडेट

Android खुली होम/अपडेट स्क्रीन पर आम तौर पर हर छह घंटे GitHub जाँचता है और असीमित Wi-Fi पर डाउनलोड कर सकता है। सिस्टम पुष्टि माँग सकता है। Mac/Linux हस्ताक्षर और हैश जाँचते हैं और स्ट्रीम समाप्त होने की प्रतीक्षा करते हैं। डेटा सुरक्षित रखें। पुराने निजी बिल्ड के लिए एक बार माइग्रेशन चाहिए।

[Update details](../UPDATES.md)

## समस्याएँ और सीमाएँ

त्रुटि पर IP, प्रोफ़ाइल, Account ID, नया PIN और नेटवर्क अलगाव जाँचें। काली स्क्रीन पर दूसरे क्लाइंट बंद करके पुनः जोड़ें। सटीक परीक्षण संस्करण नीचे हैं। इंटरनेट/VPN, स्लीप से जागना, लंबे सत्र और सभी कंट्रोलर फ़ंक्शन प्रमाणित नहीं हैं। Windows, Intel Mac और Linux x64 योजनाबद्ध हैं। Deckivo PS5 WebKit ठीक नहीं करता।

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## Deckivo को आगे बढ़ाएँ

Deckivo मुफ्त और खुला स्रोत है। आपका समर्थन नए प्लेटफ़ॉर्म और असली उपकरणों के परीक्षण में मदद करता है।

- Apple Developer ID ($99/yr) — Mac हस्ताक्षर और नोटराइज़ेशन
- Windows संस्करण
- और परीक्षण उपकरण: PS5 Pro और हैंडहेल्ड

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="फ़ोन से स्कैन करें">

सब कुछ मुफ्त रहेगा। समर्थन वैकल्पिक है।
<!-- SUPPORT:END -->
