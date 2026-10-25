# Deckivo — دليل التثبيت واللعب

Deckivo **0.6.1 preview** · 2026-10-25

[English](en.md) · [Русский](ru.md) · [Українська](uk.md) · [Polski](pl.md) · [Deutsch](de.md) · [Français](fr.md) · [Español](es.md) · [Italiano](it.md) · [Português](pt.md) · [Türkçe](tr.md) · [简体中文](zh.md) · [日本語](ja.md) · [한국어](ko.md) · [العربية](ar.md) · [हिन्दी](hi.md) · [Bahasa Indonesia](id.md)

## قبل البدء

الإصدار 0.6.1 تجريبي. صِل PS5 والعميل بالشبكة المنزلية نفسها. اختر المستخدم المطلوب على PS5 ثم الإعدادات ← النظام ← اللعب عن بُعد ← تفعيل. أبقِ الجهاز قيد التشغيل أثناء الربط الأول. يُفضّل Wi-Fi بتردد 5 غيغاهرتز؛ قد تعزل شبكة الضيوف الأجهزة.

## Android

نزّل APK بمعمارية arm64 من الإصدار. يلزم Android 8 أو أحدث؛ الاختبار الفعلي على Switch OLED مع Android 15. اسمح بالتثبيت للمصدر المختار فقط. ثبّت فوق النسخة السابقة دون حذف التطبيق أو بياناته. اختر اللغة ومعالج الاتصال، واربط يد Bluetooth من إعدادات Android. لا تعطّل Play Protect.

[Android APK](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.1/Deckivo-0.6.1-arm64.apk) · [Release / SHA-256](https://github.com/remteh-by/remteh-remote-play/releases/tag/v0.6.1)

<a id="macos"></a>

## macOS

Apple Silicon فقط. ثبّت chiaki-ng بشكل منفصل واربط PS5 ثم أغلق البث فيه. فك ZIP وانقل Deckivo.app إلى ~/Applications. التطبيق غير موثّق لدى Apple؛ قد يلزم «الفتح على أي حال» في الخصوصية والأمان. لا تعطّل Gatekeeper بالكامل. استورد تسجيل chiaki-ng في Deckivo وأدخل عنوان IP للجهاز.

[Mac ZIP · 0.6.1 b10](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.1/Deckivo-macos-0.6.1-b10.zip) · [chiaki-ng](https://github.com/streetpea/chiaki-ng/releases)

<a id="ubuntu"></a>

## Switchroot Ubuntu

معاينة للمطورين على Switchroot Ubuntu 24.04 ARM64 مع KDE/X11 وFFmpeg 6.1. يحتاج التثبيت الأول إلى المصدر الكامل وPyQt5 وGCC والتبعيات. نفّذ الأوامر أدناه من جذر المصدر ثم الربط التفاعلي. ملف ZIP الصغير لتحديث بيئة موجودة فقط. لا تستبدل تعريفات NVIDIA/FFmpeg.

```sh
# Initial runtime (complete source kit)
python3 desktop/linux/build-install.py
# Interactive pairing
python3 desktop/linux/pair.py
# Upgrade an existing runtime only
python3 desktop/linux/upgrade.py
```

[Linux requirements](../LINUX.md) · [Complete source kit](https://github.com/remteh-by/remteh-remote-play/releases/download/v0.6.1/Deckivo-0.6.1-sources.zip)

## ربط الجهاز

استخدم Account ID بصيغة Base64 للمستخدم الصحيح، وليس الاسم أو البريد. افتح اللعب عن بُعد ← ربط جهاز على PS5 وأدخل الرمز الجديد المكوّن من ثمانية أرقام قبل انتهاء الوقت. رمز مساعد ELF الاختياري مختلف. يطلب Linux البيانات تفاعليًا، ويستورد Mac تسجيل chiaki-ng. لا تنشر المفاتيح أو رمز PIN.

## التحكم والجودة

ابدأ بدقة 720p وخفّض معدل البت أو اختر 30 FPS عند ضعف الشبكة. في Android اسحب قليلًا للأعلى من الحافة السفلية لإظهار PS/Touch. في Linux زر Home هو PS وCapture هو لوحة اللمس. اختبر الصوت والعصي والزنادات والأزرار. احفظ اللعبة قبل قطع الاتصال؛ إغلاق البث لا يغلق اللعبة.

## التحديث التلقائي

يتحقق Android من GitHub أثناء فتح الشاشة الرئيسية أو التحديثات، عادة كل ست ساعات، ويمكنه التنزيل عبر Wi-Fi غير محدود. قد يطلب النظام تأكيد التثبيت. يتحقق Mac/Linux من التوقيع والبصمة وينتظر انتهاء البث. احتفظ بالبيانات. تحتاج النسخ الخاصة القديمة إلى انتقال لمرة واحدة.

[Update details](../UPDATES.md)

## المشكلات والحدود

عند الفشل تحقّق من IP والمستخدم وAccount ID ورمز جديد وعزل الشبكة. للشاشة السوداء أغلق العملاء الآخرين وأعد الاتصال. الإصدارات المختبرة موضحة أدناه. الإنترنت/VPN والاستيقاظ والجلسات الطويلة وكل وظائف التحكم غير معتمدة. Windows وIntel Mac وLinux x64 مخططة. لا يصلح Deckivo متصفح WebKit في PS5.

[Device / version / scope](../TESTED.md) · [Technical reference](../TECHNICAL.md)

<!-- SUPPORT:START -->
## ساعد Deckivo على النمو

Deckivo مجاني ومفتوح المصدر. يساعد دعمك في المنصات الجديدة والاختبارات على أجهزة حقيقية.

- Apple Developer ID ($99/yr) — توقيع وتوثيق Mac
- إصدار Windows
- أجهزة اختبار أكثر: PS5 Pro وأجهزة محمولة

[Ko-fi · RemTeh](https://ko-fi.com/pavelzayats)

<img src="../../website/assets/support/kofi.svg" width="180" height="180" alt="امسح بهاتفك">

يبقى كل شيء مجانيًا. الدعم اختياري.
<!-- SUPPORT:END -->
