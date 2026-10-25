# Android cleartext inventory — 0.6.1

- `LanSetupActivity`: Java `HttpURLConnection` to the user's validated private
  console IPv4 address, `/v1/status` and `/v1/account` on port 38080. Redirects
  are disabled; the account request has the local one-use helper code.
- The same helper is sent over a Java TCP socket to console port 9021; a
  connectivity probe uses TCP 9295. These are LAN-only setup actions.
- `UpdateHttp` uses HTTPS GitHub API/release assets in public mode. The explicit
  older private-preview channel may use a validated local HTTP base; it remains
  separate from the default public channel.
- Discovery, registration, wakeup and streaming use native Chiaki sockets.
  Android Network Security Config does not filter these native sockets.
- No WebView is used by Deckivo's Java/Kotlin setup/update UI.

Because the Java helper genuinely needs HTTP to a console IP, this release keeps
`usesCleartextTraffic=true`, as required by the task's conditional rule. NSC
cannot express an arbitrary private CIDR allowlist; setting a global HTTPS-only
base would break the helper. The app validates the LAN address in `LanRules`.
This is not a Sony update firewall or a promise of Internet-play security.
