# Deckivo public website

Static site deployed by `.github/workflows/pages.yml` to
https://remteh-by.github.io/remteh-remote-play/.

Local preview:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory website
```

No build service, analytics, third-party script or account form is needed.
Local storage holds the selected language. English is the first-visit default;
Auto follows browser preferences. Primary copy has 16 languages; exact technical
notes are English/Russian. All 16 linked setup guides contain platform steps.
Website catalogs are in `localization/site.json`; `content.js` is their compiled
copy. Shared app catalogs are a separate generator input.

The original Sony PS5 product photo is displayed proportionally. Source and
SHA-256 are in `assets/source.json`, with notices alongside it. The GitHub cover
is a screenshot of this implemented page; no private console screenshot is used.

Ko-fi points to the existing RemTeh profile. GitHub funding is configured in
`.github/FUNDING.yml`. The Pages `updates/` directory contains RSA-signed native
metadata; private signing keys and device registrations never belong here.

See `docs/design/PUBLIC-REVIEW.md` for responsive/design checks and
`docs/TESTED.md` for exact hardware/build evidence. Public 0.x builds remain
experimental; deployment does not certify Internet play or every device.
