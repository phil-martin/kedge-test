# auth-test-3: multi-service

A public `web` service (python, serves a page and `/call`) behind an auth policy,
plus a private `inner` service (traefik/whoami, `expose` only). `/call` reports the
headers `web` received from the platform, calls `http://inner/`, and includes inner's
echo — showing whether identity headers exist at either hop.

Expected per /docs/compose: web receives X-Kedge-Auth-* for the signed-in caller.

Observed (signed in, pressing "test auth" which tries three upstream namings):

- `reverse_proxy inner:80` (bare sibling name, as documented in /docs/network): **502**
- `reverse_proxy phil-martin-kedge-test-auth-3-inner:80` (full app name): **502**
- `reverse_proxy https://phil-martin-kedge-test-auth-3-inner.kedge.run` (public
  hostname): **200** — inner's echo shows the forwarded browser headers plus
  `Via`/`X-Forwarded-*`/`X-Kedge-Dc`/`X-Kedge-Restore`, and **no `X-Kedge-Auth-*`**
  anywhere, despite the originating request being authenticated at `web`.

Additional observations:

- `inner` uses `expose` only, but is publicly reachable at
  https://phil-martin-kedge-test-auth-3-inner.kedge.run (docs: "expose remains
  private").
- A python:3.12-slim `http.server` web service repeatedly failed the readiness gate
  (`timeout waiting for <ip>:8000`); nginx failed at "Creating snapshot"; the
  single-process caddy binary deployed fine.
