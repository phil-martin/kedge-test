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
(`auth-test-1/whoami-identity`, structured comment form from /docs/handlers). Deploying
that file as a handler is rejected with:

```
whoami-identity: kedge metadata identity: property does not apply to a handler
```

so it is kept non-executable (ships as source, not a route).

A fuller test matrix (CGI handlers, standalone functions, container services — all
identity-blind) is documented in the life-app repo:
`docs/kedge-auth-findings.md`.
