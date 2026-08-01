"""Tests for the crypto in ./api. Run: python3 test_auth.py"""
import importlib.util, os, sys, tempfile, time, unittest

os.environ["AUTH_DB"] = ":memory:"
spec = importlib.util.spec_from_loader("api", loader=None)
api = importlib.util.module_from_spec(spec)
src = open("api").read().replace("\nmain()\n", "\n")  # import without running
exec(compile(src, "api", "exec"), api.__dict__)

SECRET = b"test-secret-key-0123456789"


class TestPasswords(unittest.TestCase):
    def test_roundtrip(self):
        h = api.hash_password("correct horse battery")
        self.assertTrue(api.verify_password("correct horse battery", h))
        self.assertFalse(api.verify_password("wrong password", h))

    def test_salted(self):
        self.assertNotEqual(api.hash_password("same"), api.hash_password("same"))

    def test_garbage_hash_rejected(self):
        self.assertFalse(api.verify_password("x", "not-a-hash"))
        self.assertFalse(api.verify_password("x", ""))
        self.assertFalse(api.verify_password("x", "bogus$aa$bb"))

    def test_both_schemes_verify(self):
        import hashlib as _h
        salt = b"0123456789abcdef"
        pb = f"pbkdf2${salt.hex()}${api._derive('pbkdf2', 'pw', salt)}"
        self.assertTrue(api.verify_password("pw", pb))
        self.assertFalse(api.verify_password("nope", pb))
        if api.HAVE_SCRYPT:
            sc = f"scrypt${salt.hex()}${api._derive('scrypt', 'pw', salt)}"
            self.assertTrue(api.verify_password("pw", sc))


class TestJWT(unittest.TestCase):
    def test_roundtrip(self):
        t = api.mint_jwt(42, "a@b.com", SECRET)
        p = api.verify_jwt(t, SECRET)
        self.assertEqual(p["sub"], "42")
        self.assertEqual(p["email"], "a@b.com")

    def test_wrong_secret_rejected(self):
        t = api.mint_jwt(1, "a@b.com", SECRET)
        self.assertIsNone(api.verify_jwt(t, b"different-secret"))

    def test_tampered_payload_rejected(self):
        t = api.mint_jwt(1, "a@b.com", SECRET)
        h, p, s = t.split(".")
        forged = api.b64url(b'{"sub":"999","email":"evil@b.com","iat":0,"exp":9999999999}')
        self.assertIsNone(api.verify_jwt(f"{h}.{forged}.{s}", SECRET))

    def test_alg_none_rejected(self):
        # classic JWT attack: swap alg to none and drop the signature
        h = api.b64url(b'{"alg":"none","typ":"JWT"}')
        p = api.b64url(b'{"sub":"1","email":"e@x.com","iat":0,"exp":9999999999}')
        self.assertIsNone(api.verify_jwt(f"{h}.{p}.", SECRET))
        self.assertIsNone(api.verify_jwt(f"{h}.{p}.anything", SECRET))

    def test_expired_rejected(self):
        past = int(time.time()) - api.TOKEN_TTL - 10
        t = api.mint_jwt(1, "a@b.com", SECRET, now=past)
        self.assertIsNone(api.verify_jwt(t, SECRET))

    def test_malformed_rejected(self):
        for bad in ["", "a", "a.b", "a.b.c", "...", "x" * 100]:
            self.assertIsNone(api.verify_jwt(bad, SECRET))


class TestSecret(unittest.TestCase):
    def test_env_wins(self):
        os.environ["AUTH_SECRET"] = "from-env"
        try:
            self.assertEqual(api.get_secret(), b"from-env")
        finally:
            del os.environ["AUTH_SECRET"]

    def test_file_generated_and_stable(self):
        with tempfile.TemporaryDirectory() as d:
            api.SECRET_FILE = os.path.join(d, "secret")
            first = api.get_secret()
            self.assertEqual(len(first), 32)
            self.assertEqual(api.get_secret(), first)  # stable across calls
            self.assertEqual(oct(os.stat(api.SECRET_FILE).st_mode)[-3:], "600")


if __name__ == "__main__":
    unittest.main(verbosity=2)
