import json
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGE = """<!doctype html>
<title>kedge auth test 3</title>
<style>body{font-family:sans-serif;max-width:46rem;margin:0 auto;padding:2rem 1rem}
pre{background:#f2f2f2;border:1px solid #ddd;border-radius:8px;padding:1rem;overflow-x:auto;font-size:.8rem}
button{font:inherit;padding:.5rem 1rem}</style>
<h1>kedge auth test 3: multi-service</h1>
<p>The public <code>web</code> service reports the headers it received, then calls the
internal <code>inner</code> service (traefik/whoami) and shows what survived the hop.</p>
<form method="post" action="/_kedge/auth/logout" style="display:inline"><button>logout</button></form>
<button id="t">test auth</button>
<h2>Result</h2><pre id="out">press "test auth"</pre>
<script>
document.getElementById('t').onclick = async () => {
  const el = document.getElementById('out');
  el.textContent = 'requesting...';
  const r = await fetch('/call');
  el.textContent = 'HTTP ' + r.status + '\\n\\n' + await r.text();
};
</script>"""


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/call":
            web_headers = {k: v for k, v in self.headers.items() if k.lower() != "cookie"}
            try:
                with urllib.request.urlopen("http://inner:80/", timeout=5) as resp:
                    inner_echo = resp.read().decode()
            except Exception as e:
                inner_echo = f"error calling inner: {e}"
            self._send(200, json.dumps({
                "web_service_received_headers": web_headers,
                "web_cookie_header_present": any(k.lower() == "cookie" for k in self.headers),
                "inner_service_echo": inner_echo,
            }, indent=1), "application/json")
        else:
            self._send(200, PAGE, "text/html")


print("listening on 8000", flush=True)
HTTPServer(("0.0.0.0", 8000), H).serve_forever()
