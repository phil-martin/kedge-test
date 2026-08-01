# Handover: test Go (and Rust) source builds against /shared.db

## Why
Python's `sqlite3` module crashes kedge handlers on `connect()` (see
auth-test-4/README.md, finding 2). Ruby works in-process (finding 5). Go/Rust are
untested. https://kedge.dev/docs/builds says source is auto-detected and built.

## Task
Create `auth-test-5/` (deploy pattern below) with a small Go HTTP service that:
1. opens `/shared.db`, runs `SELECT 42`, lists tables, returns JSON;
2. is built TWICE for comparison — default driver (`modernc.org/sqlite` or plain
   `mattn/go-sqlite3`) vs `mattn/go-sqlite3` with `-tags=libsqlite3`.
Docs say statically-embedded SQLite cannot be intercepted; the tags build links the
system libsqlite3 and should work. Confirm which (if either) actually works.

## Watch out for
- **Readiness gate**: services must `listen()` promptly. python http.server and nginx
  both failed; single-process Go binaries (caddy) succeeded. Go should be fine.
- **Prebuilt images are rejected** ("not a Nydus image") — build from source or a
  Dockerfile, never a bare `image:` from Docker Hub.
- **Replicated tables**: every table needs a PRIMARY KEY; UNIQUE columns are rejected.
- Sibling-service DNS (`inner:80`) does not resolve (auth-test-3) — single service is
  simplest.

## Deploy pattern (subtree push per app folder)
```
git remote add kedge-auth-5 ssh://kedge.dev/phil-martin/kedge-test-auth-5.git
git push kedge-auth-5 $(git subtree split --prefix=auth-test-5 HEAD):refs/heads/main
```

## If Go works
It becomes the best candidate for the real auth service (fast, single binary, passes
the readiness gate, in-process DB). Port the logic in `auth-test-4/api` — scrypt/PBKDF2
password hashing, HS256 JWTs, email as PRIMARY KEY — which is live and verified at
https://phil-martin-kedge-test-auth-4.kedge.run

## Wider context
life-app (~/code/life-app) is the real app; read its CLAUDE.md and docs/PLATFORM.md.
It currently uses kedge managed collections because backend code never receives
identity. DIY auth (auth-test-4) is the escape hatch; it needs rate limiting, email
validation, password reset/verification, token revocation, and AUTH_SECRET set via
`kedge env` before production use.
