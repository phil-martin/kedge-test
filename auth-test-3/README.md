# auth-test-3: multi-service

A public `web` service (python, serves a page and `/call`) behind an auth policy,
plus a private `inner` service (traefik/whoami, `expose` only). `/call` reports the
headers `web` received from the platform, calls `http://inner/`, and includes inner's
echo — showing whether identity headers exist at either hop.

Expected per /docs/compose: web receives X-Kedge-Auth-* for the signed-in caller.

Observed: (filled in after deployment)
