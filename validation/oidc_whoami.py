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
REDIRECT_URI = "http://127.0.0.1:8765/callback" # TODO: replace with the redirect URI of the client
SCOPE        = "openid profile email"

# ---- discovery ----
discovery = requests.get(
    f"{ISSUER.rstrip('/')}/api/.well-known/openid-configuration"
).json()

state = secrets.token_urlsafe(16)
nonce = secrets.token_urlsafe(16)

client = OAuth2Session(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scope=SCOPE,
    redirect_uri=REDIRECT_URI,
)

auth_url, code_verifier, _ = client.create_authorization_url(
    discovery["authorization_endpoint"],
    state=state,
    nonce=nonce,
    code_challenge_method="S256",
)

# ---- tiny callback server ----
class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
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
        self.end_headers()
        self.wfile.write(b"Login successful. You can close this window.\n")

        print(json.dumps(id_token.claims, indent=2))
        sys.exit(0)

# ---- run ----
print("Opening browser for login...")
webbrowser.open(auth_url)

HTTPServer(("127.0.0.1", 8765), CallbackHandler).serve_forever()
