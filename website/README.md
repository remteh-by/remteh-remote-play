# Deckivo website — local preview only

Static GitHub Pages-ready site. Start locally from the repository:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory website
```

Visit `http://127.0.0.1:8765/`. No build service, analytics, cookies, signup form, payment backend or secret is required. Local storage holds only the selected language. English is the first-visit default. Regenerate shared translations with `python3 scripts/generate-localizations.py`.

No Pages workflow is enabled. `noindex,nofollow` is intentional while this is a private preview. Remove the preview indexing block only as part of the approved 1.0.0 publication. Existing repository history links do not publish the new work. Payment destination is not configured; the support section explains the actual state.

Hero image was generated for this project with Image Gen. It depicts a fictional handheld and generic landscape, not an existing game. The website preview is HTML with example data; it does not connect to a console. Keep all app/session keys and private device screenshots out of this directory.
