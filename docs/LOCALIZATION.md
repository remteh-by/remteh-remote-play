# Language support

English is the deliberate first-launch default, independent of OS/browser language. The native home screen and toolbars expose a language selector; the site header exposes the same 16 choices. Selection persists locally. Optional Automatic mode chooses the first supported system/browser language; unsupported or empty preference lists fall back to English. Explicit manual choice always wins. Regional variants use the available base language (e.g. pt-BR → pt; Chinese variants use the current Simplified Chinese pack). Arabic uses RTL. Android 13+ applies app language through LocaleManager; earlier Android uses AppCompat. The Activity context is localized before UI inflation so the first frame and process-restored screens use the saved choice even while the framework applies its initial language update. The Automatic option re-evaluates system preferences on configuration changes. No translation request is made by the shipped app or website.

Languages: en, ru, uk, pl, de, fr, es, it, pt, tr, zh (Simplified Chinese), ja, ko, ar, hi, id.

## Sources

- `localization/<code>.json`: 98 shared app/site strings drafted per language.
- `localization/native-extra.json`: original English/Russian setup and About copy.
- `localization/android/<code>.json`: 139 additional native strings, including legacy dialogs/preferences. Missing translations were drafted using Google Translate on 2026-10-24 from public UI copy only; no console registration database, keys or account IDs were sent. Russian existing copy is retained. These translations are **drafts requiring linguistic review**, not certified translations.
- `scripts/generate-localizations.py`: validates catalog keys and printf placeholders, generates Android resource files and `website/locales.js`. Android uses the legacy `values-in` qualifier for Indonesian; picker code is `id`.

Run the generator after source edits. Do not hand-edit generated XML or `locales.js`. Android resource identifiers, preference keys, device/model names, protocol terms and URLs must never be translated. Technical exception details, native library diagnostics and certain controller event labels remain in English for debugging; they are not a missing runtime language pack.

## Review before 1.0.0

Native speakers should review terminology, politeness, Android/PS5 navigation labels, donation wording and long strings. Verify registration and update errors on device, Arabic mixed text and numbers, CJK wrapping, Devanagari marks and 1.3×/large font settings. Check at least phone portrait, Switch landscape and desktop widths. Do not call all-language visual/linguistic acceptance complete just because catalogs are present.

New desktop clients should consume these catalogs through a platform adapter. Native desktop implementations do not yet exist in this checkout.

Implementation reference: [Android per-app language preferences](https://developer.android.com/guide/topics/resources/app-languages).

## Public 0.6.0 documentation

`localization/guides.json` is the source for 16 complete platform/setup guides in
`docs/guides/`. English/Russian include extended explanations. `localization/site.json`
contains the public landing page copy; its primary narrative is translated into
16 languages. Exact technical evidence/download notes currently remain English
for languages other than English/Russian. New native desktop-specific controls
also have English/Russian coverage with English fallback elsewhere. No claim of
professional translation or full per-language physical acceptance is made.
