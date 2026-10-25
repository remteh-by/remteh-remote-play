# Deckivo static website

Pages deploys `build/site`, generated from `website/template.html`,
`localization/site.json`, `localization/downloads.json`, `design-system/site.json`
and the shared support config.
The root is English; 15 native language URLs include full HTML, metadata,
canonical/hreflang and visible FAQ content without JavaScript. Auto only suggests
another URL. Arabic is RTL. No language redirect or local-storage dependency.

```sh
python3 -m venv .build-tools
.build-tools/bin/pip install -r scripts/requirements-build.txt
.build-tools/bin/python scripts/generate-support.py
.build-tools/bin/python scripts/build-site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory build/site
```

The optional `--download-stats PATH` argument accepts the validated snapshot
produced by `scripts/download-stats.py`. A supplied malformed or inconsistent
snapshot stops the build; omitting it keeps local builds working and renders a
clear “statistics unavailable” state. With or without a snapshot, the build
writes `download-stats.json` and a local `assets/downloads.svg` badge. The
scheduled Pages workflow supplies a fresh snapshot, so the browser makes no
API or analytics request to render these totals.

The prominent number is the sum of Android, macOS, Linux and bundle package
downloads. The all-files total and per-release tables also include source,
update-metadata and other release assets. GitHub counts file downloads rather
than unique people or installations, so repeated downloads, automatic updates
and maintainer checks are included.

Artwork: actual isolated Qt setup UI, AVIF with WebP fallback; cover is composed
from that capture, preserving the actual console photograph used by the app.
`assets/screenshot.json` records the exact version/build, source revision and
image hashes. Development previews are labelled separately from public downloads.
An outdated screenshot is a release-blocking defect; refresh it after UI changes.
To refresh the capture, use `scripts/capture-preview.py` with a Qt-capable Python,
then `scripts/build-site-assets.py --capture-only` with the documented build dependencies.
Use `--source-root /path/to/checkout` when capturing a separate development checkout.
The Pages build validates image SHA-256 against the screenshot manifest and fails
on mismatches. Inspect the actual image and version caption before publication.
The WOFF2 is a Latin/Cyrillic IBM Plex Sans subset renamed Deckivo Sans Subset under the included OFL. CJK,
Arabic and Hindi use system fonts and do not preload the web font.

Only enabled owner-supplied support methods are rendered. Empty raised amounts
are explicitly unknown; no received donations are invented. Empty supporters
stay hidden. Ko-fi is the existing RemTeh profile, not a new account.

`site.analytics.goatcounter` is empty: **no analytics script/request is loaded**.
Download totals come from the scheduled server-side GitHub snapshot described
above, not from visitor tracking. If browser analytics is ever enabled, review
the [counter API](https://www.goatcounter.com/help/events) and
[privacy policy](https://www.goatcounter.com/help/privacy) first.

No CNAME is shipped. See [domain migration](../docs/marketing/domain.md): adding
one to the old Pages project strands 0.6.0 desktop updaters. The signed `updates/`
files and pinned public RSA key remain on the legacy channel.
