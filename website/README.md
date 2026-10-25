# Deckivo static website

Pages deploys `build/site`, generated from `website/template.html`,
`localization/site.json`, `design-system/site.json` and the shared support config.
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

Artwork: actual isolated Qt setup UI, AVIF with WebP fallback; cover is composed
from that capture. The neutral vector is our own. No Sony press image remains.
To refresh the capture, use `scripts/capture-preview.py` with a Qt-capable Python,
then `scripts/build-site-assets.py` with the documented build dependencies.
The WOFF2 is a Latin/Cyrillic IBM Plex Sans subset under the included OFL. CJK,
Arabic and Hindi use system fonts and do not preload the web font.

Only enabled owner-supplied support methods are rendered. Empty raised amounts
are explicitly unknown; no received donations are invented. Empty supporters
stay hidden. Ko-fi is the existing RemTeh profile, not a new account.

`site.analytics.goatcounter` is empty: **no analytics script/request is loaded**.
When the owner enables it, public visits and download/support/guide clicks can
be counted. The code omits query/hash/referrer and pairing data; it does not
promise that a network counter never processes an IP address. Review the
[counter API](https://www.goatcounter.com/help/events) and
[privacy policy](https://www.goatcounter.com/help/privacy) before activation.

No CNAME is shipped. See [domain migration](../docs/marketing/domain.md): adding
one to the old Pages project strands 0.6.0 desktop updaters. The signed `updates/`
files and pinned public RSA key remain on the legacy channel.
