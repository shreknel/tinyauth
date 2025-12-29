#!/usr/bin/env python3
import os
import sys
import json
import webbrowser
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests
from authlib.integrations.requests_client import OAuth2Session
from authlib.oidc.core import CodeIDToken

# ---- config via env ----
ISSUER        = os.environ["OIDC_ISSUER"]
CLIENT_ID    = os.environ["CLIENT_ID"]
CLIENT_SECRET= os.environ.get("CLIENT_SECRET")  # optional (public clients ok)
REDIRECT_URI = "http://client.aande.top/callback"
SCOPE        = "openid profile email"

# ---- discovery ----
# Retry discovery in case nginx isn't ready yet
discovery = None
for attempt in range(10):
    try:
        discovery = requests.get(
            f"{ISSUER.rstrip('/')}/api/.well-known/openid-configuration",
            timeout=5
        ).json()
        break
    except Exception as e:
        if attempt < 9:
            print(f"Discovery attempt {attempt + 1} failed: {e}, retrying...")
            import time
            time.sleep(2)
        else:
            raise

if discovery is None:
    raise RuntimeError("Failed to fetch OIDC discovery document after 10 attempts")

state = secrets.token_urlsafe(16)
nonce = secrets.token_urlsafe(16)

client = OAuth2Session(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scope=SCOPE,
    redirect_uri=REDIRECT_URI,
)

auth_result = client.create_authorization_url(
    discovery["authorization_endpoint"],
    state=state,
    nonce=nonce,
    code_challenge_method="S256",
)
auth_url = auth_result[0]
code_verifier = auth_result[1] if len(auth_result) > 1 else None

# ---- tiny callback server ----
class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Handle root path - show authorization URL
        if self.path == "/" or self.path == "":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>OIDC Test Client</title></head>
            <body>
                <h1>OIDC Test Client</h1>
                <p>Click the button below to start the OIDC flow:</p>
                <a href="{auth_url}" style="display: inline-block; padding: 10px 20px; background: #4285f4; color: white; text-decoration: none; border-radius: 4px;">Login with OIDC</a>
                <hr>
                <p><small>Authorization URL: <code>{auth_url}</code></small></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            return

        # Handle callback
        if not self.path.startswith("/callback"):
            self.send_error(404, "Not Found")
            return

        qs = parse_qs(urlparse(self.path).query)

        if qs.get("state", [None])[0] != state:
            self.send_error(400, "Invalid state")
            return

        code = qs.get("code", [None])[0]
        if not code:
            self.send_error(400, "Missing code")
            return

        token = client.fetch_token(
            discovery["token_endpoint"],
            code=code,
            code_verifier=code_verifier,
        )

        # ---- ID token validation ----
        id_token = CodeIDToken(
            token["id_token"],
            client_id=CLIENT_ID,
            issuer=discovery["issuer"],
            nonce=nonce,
            jwk_set=requests.get(discovery["jwks_uri"]).json(),
        )

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>OIDC Login Successful</title></head>
        <body>
            <h1>✅ Login Successful!</h1>
            <p>You can close this window.</p>
            <hr>
            <h2>ID Token Claims:</h2>
            <pre>{json.dumps(id_token.claims, indent=2)}</pre>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

        print(json.dumps(id_token.claims, indent=2))
        sys.exit(0)

# ---- run ----
print("=" * 60)
print("OIDC Test Client")
print("=" * 60)
print(f"\nAuthorization URL: {auth_url}")
print("\nTo test the OIDC flow:")
print("1. Open the authorization URL above in your browser")
print("2. Login with credentials: user / pass")
print("3. You will be redirected back to the callback")
print("4. The ID token claims will be displayed below")
print(f"\nWaiting for callback on {REDIRECT_URI}...")
print("=" * 60)

# Try to open browser (may fail in Docker, that's OK)
try:
    webbrowser.open(auth_url)
except Exception as e:
    print(f"Could not open browser automatically: {e}")
    print("Please open the authorization URL manually")

HTTPServer(("0.0.0.0", 8765), CallbackHandler).serve_forever()
