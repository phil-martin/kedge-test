# auth-test-4: DIY email+password auth on kedge

Working replacement for kedge's auth, built because kedge never delivers identity to
backend code (auth-test-1/2/3). No kedge auth policy is used at all.

- **Passwords**: scrypt when available, else PBKDF2-HMAC-SHA256 (600k rounds), salted,
  scheme-tagged so hashes can be upgraded.
- **Sessions**: self-minted HS256 JWTs (pure `hmac`/`hashlib`), 30-day expiry, sent as
  `Authorization: Bearer`. Verified in the handler, which then keys per-user rows on
  the token subject.
- **Secret**: `AUTH_SECRET` env var, else a 32-byte random file created at
  `/shared/auth_secret` (0600) on first use.
- `test_auth.py` — 12 unit tests for the crypto (run from this directory).

Live: https://phil-martin-kedge-test-auth-4.kedge.run

## Verified live

signup / login / me round-trip; per-user counter increments across requests;
duplicate signup 409; wrong password and unknown user both 401 with identical
messages (no user enumeration, dummy-hash verify keeps timing constant); missing,
garbage, tampered-signature, and `alg:none` tokens all rejected; SQL injection
attempt stored as a literal string with the table intact.

## Platform findings (the reason this file looks the way it does)

1. **`Authorization` headers DO reach handlers** (`HTTP_AUTHORIZATION`), which is what
   makes DIY auth possible at all.
2. **Python's `sqlite3` module cannot be used in a handler.** Any `connect()` — even
   `":memory:"` — kills the process (HTTP 502, no traceback), apparently via the
   `LD_PRELOAD` replication shim. The docs say Python's stdlib "works transparently".
   Workaround: shell out to the `sqlite3` CLI, which works. Values are passed as
   `CAST(x'<hex>' AS TEXT)` literals, which cannot carry an injection.
3. **Replicated tables require a PRIMARY KEY** — `CREATE TABLE t(x)` is rejected with
   `DDL admission rejected: replicated tables require PRIMARY KEY`.
4. **`UNIQUE` columns are rejected**: `a NOT NULL UNIQUE (coordinated) key ... requires
   a reservation backend; none is configured`. Uniqueness must come from the PRIMARY
   KEY (hence email as PK, which also avoids auto-increment ids in a multi-region
   replicated database).
5. `/shared/` filesystem writes work normally; PBKDF2 is fast (~7ms per 50k rounds).

## Not production-ready yet

Email validation is minimal (an `@` check); no rate limiting on login; no password
reset, email verification, or token revocation; secret is per-app-instance unless
`AUTH_SECRET` is set. These are the next steps if this pattern moves into life-app.
