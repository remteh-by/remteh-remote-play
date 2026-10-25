# Deckivo design system — private 0.2.0 candidate

## Direction

Dark, calm Remote Play client with a navy base, mint actions and an original D/play mark. Native app: persistent navigation, readable console state, one primary action, clearly accessible language selection. Website: large editorial hero, supplied aurora/handheld artwork, native HTML text and controls, a console preview, numbered features, honest platform availability and optional support.

## Tokens and components

- Canvas `#080F16`, surface `#101D29`, raised `#182B38`, border `#2A414F`.
- Text `#EAF4F7`, secondary `#A5BAC7`, action `#5AE0CA`, action text `#061B1A`.
- Android spacing: 8 / 12 / 16 / 20 / 28 dp; button target at least 48 dp. Cards 20–24 dp radius; buttons 14 dp radius.
- Android typography: native sans-serif, 30–32 sp page titles, 19–24 sp card headings, 14–16 sp body. System font fallback for CJK/Arabic/Devanagari.
- Website: fluid gutters and typography, responsive grids; no 1200px fixed page bottleneck on 4K.
- Shared components: console card; primary/secondary button; native toolbar with back and language actions; titled panels; outlined field; settings tabs; hidden stream controls; language selector; support status.

## States and accessibility

Discovery distinguishes online, rest, registered-but-unknown and unregistered. Unknown state is not reported as online. Download controls use actual update state. Support has informative text until a real payment destination is configured, rather than a non-functional Pay button.

Use start/end alignment and RTL for Arabic. Preserve visible controller/keyboard focus, readable text, native select/dialog controls and reduced-motion preferences on the website. The streaming overlay remains hidden until requested; permanent white PS/Touch rectangles are not restored.

## Fidelity ledger against generated concepts

| Anchor | Implemented | Reason for intentional difference |
|---|---|---|
| Full-width aurora handheld hero, left headline | Yes; standalone image asset plus HTML | English default and translated text requested after concept generation |
| Navy/white/mint palette, large typography | Same direction in app and website | Native Android uses system fonts for multilingual coverage |
| Logo and restrained header navigation | Implemented with original D mark | Visible language selector and support section added at owner request |
| App preview beside three numbered feature rows | Implemented as HTML, not a flattened screenshot | Shows new actual app structure rather than unverified PS5 artwork/data |
| Four platform columns | Android testing, desktop planned | Removes generated claims that desktop versions already exist |
| Open-source footer and RemTeh credit | Preserved, links without tracking parameters | No customer lead generation or paid support promises |
| New support and roadmap sections | Added consistently with the same tokens | Latest owner requirements; no payment processing enabled |

The artwork is a fictional generic handheld illustration, not evidence of a supported hardware SKU or an actual game screenshot. App preview uses example console data. Screenshots of the user's paired console are private QA evidence outside the repository.
