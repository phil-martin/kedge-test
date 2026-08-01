# kedge-test

Minimal, self-contained test apps for diagnosing and demonstrating Kedge platform
behaviour. Each numbered folder is an independent app deployable with
`kedge up --name <app-name>` from inside the folder.

## auth-test-1

**Bug demonstrated**: backend workloads never receive the authenticated caller's
identity, despite the documentation stating that handlers "receive verified identity
as environment variables" (`KEDGE_AUTH_SUBJECT`, `KEDGE_AUTH_EMAIL`,
`KEDGE_AUTH_PROVIDER`, `KEDGE_AUTH_ASSERTION`) when an app auth policy gates the
route.

Structure:
- `compose.yaml` — auth policy gating `/whoami` (open Google/GitHub sign-in)
- `whoami` — python3 `handler(req)` worker that reports every auth-related env var
  and request header it can see
- `index.html` — public page with login / logout / test-auth controls; shows the
  frontend's view (`/_kedge/auth/me`) alongside the worker's view

Expected per docs: after login, "test auth" shows `KEDGE_AUTH_*` values for the
signed-in user.

Observed: the gate works (logged out → 401 `authentication_required`; logged in →
200), but the worker sees **no identity at all** — `auth_env_vars_found` is empty,
no `X-Kedge-Auth-*` headers, no cookie — while `/_kedge/auth/me` on the same origin
identifies the user. This makes per-user backend code (e.g. SQLite keyed by user)
impossible.

Also tried: setting the `identity` property in the handler configuration
(`auth-test-1-rejected/whoami-identity`, structured comment form from /docs/handlers).
Any tree containing that file is rejected at deploy with:

```
whoami-identity: kedge metadata identity: property does not apply to a handler
```

so it lives outside the deployed folder (kedge treats any file starting with `#!`
as a handler, whatever its name or permissions).

A fuller test matrix (CGI handlers, standalone functions, container services — all
identity-blind) is documented in the life-app repo:
`docs/kedge-auth-findings.md`.

## auth-test-2

Container-service variant of the same question. A stock `traefik/whoami` container
(echoes all request headers) behind an auth policy. /docs/compose says services
receive `X-Kedge-Auth-Subject/-Email/-Provider/-Assertion`; signed-in requests show
only `X-Kedge-Dc` / `X-Kedge-Restore` / `X-Forwarded-For`.

Live: https://phil-martin-kedge-test-auth-2.kedge.run (sign in; the page is the
container's header echo).

## auth-test-3

Multi-service compose: an auth-gated public `web` (caddy) proxying `/call` to a
private `inner` (traefik/whoami). Live:
https://phil-martin-kedge-test-auth-3-web.kedge.run

Findings: no `X-Kedge-Auth-*` headers at either hop; sibling-name private networking
(`inner:80`) returns 502 and only the public hostname connects; the `expose`-only
service is publicly reachable. Details in auth-test-3/README.md.

## auth-test-4

A **working** DIY auth implementation (email+password, hashed credentials in the
shared SQLite, self-minted HS256 JWTs) proving that per-user backend code is possible
on kedge without its auth. Also documents that Python's `sqlite3` module crashes
handlers and that replicated tables reject `UNIQUE` columns and tables without a
PRIMARY KEY. See auth-test-4/README.md.
