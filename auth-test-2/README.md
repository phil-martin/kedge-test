# auth-test-2: container service

From /docs/compose:

> Container services receive:
> X-Kedge-Auth-Subject / X-Kedge-Auth-Email / X-Kedge-Auth-Provider / X-Kedge-Auth-Assertion

This app is a single `traefik/whoami` container (stock image, echoes all request
headers) behind an auth policy covering every route.

To test: visit the app, sign in with any Google or GitHub account, and read the
echoed headers. Sign out with `POST /_kedge/auth/logout` if needed.

Expected: the echo includes the X-Kedge-Auth-* headers for the signed-in user.

Observed (signed in via GitHub): the echo contains only

```
X-Forwarded-For: <ips>
X-Kedge-Dc: hil
X-Kedge-Restore: warm
X-Kedge-Restore-Ms: 3.5
```

No X-Kedge-Auth-* headers are present.
