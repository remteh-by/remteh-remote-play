# Future domain — deliberately not activated in 0.6.1

No CNAME file, DNS write or Pages domain setting belongs to this release.
The canonical base is `design-system/site.json → site.base_url`.
All local page assets and language links are relative.

0.6.1 desktop trusts a redirect only from the two exact old metadata URLs:
`https://remteh-by.github.io/remteh-remote-play/updates/index.json` and
`index.sig` to their equivalents under `https://deckivo.remteh.by/updates/`.
RSA verification still uses the same pinned key. Other metadata redirects,
HTTP, query strings and a different hostname/path are rejected.
Android's public channel is GitHub Releases API (`UpdatePolicy.API_URL`) and
exact GitHub release assets; the Pages domain is not its update channel.

## Before changing anything

0.6.0 desktop rejects the Pages → new-domain redirect. GitHub Pages starts that
redirect when a CNAME is applied to this existing project. Waiting for “90%”
would still strand the rest, and this project has no installed-version telemetry
to measure 90%. Do not treat it as an acceptance threshold.

Preferred plan: publish the new domain using a **separate Pages deployment**,
keep this legacy Pages project and its signed `/updates/` files alive, and move
website links/canonicals deliberately. That preserves updates for old clients.
The new deployment can use the same generated site and signed metadata.

If the owner knowingly retires the legacy channel instead:
1. Distribute 0.6.1+ and provide an explicit manual upgrade route to every old desktop user.
2. Confirm the new HTTPS host serves the exact signed index and packages.
3. Owner sets `deckivo.remteh.by CNAME remteh-by.github.io` and configures the new Pages deployment.
4. Only then add its CNAME file and change the one canonical base variable.
5. Validate TLS, every language URL, old-channel compatibility and both updater clients.

The DNS record is an owner input for a future deployment, not an instruction to activate it now.
