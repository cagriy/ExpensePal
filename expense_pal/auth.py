import json
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests

from expense_pal.config import (
    BASE_URL,
    TOKEN_PATH,
    CALLBACK_URL,
    CALLBACK_PORT,
    CLIENT_ID,
    CLIENT_SECRET,
)


def get_access_token() -> str:
    """Return a valid access token, refreshing or re-authorizing as needed."""
    tokens = _load_tokens()
    if tokens:
        if tokens.get("expires_at", 0) > time.time() + 60:
            return tokens["access_token"]
        if tokens.get("refresh_token"):
            refreshed = _refresh_token(tokens["refresh_token"])
            if refreshed:
                return refreshed["access_token"]
    tokens = _authorize()
    return tokens["access_token"]


def _load_tokens() -> dict | None:
    if TOKEN_PATH.exists():
        return json.loads(TOKEN_PATH.read_text())
    return None


def _save_tokens(token_response: dict) -> dict:
    tokens = {
        "access_token": token_response["access_token"],
        "refresh_token": token_response["refresh_token"],
        "expires_at": time.time() + token_response["expires_in"],
    }
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(tokens, indent=2))
    return tokens


def _authorize() -> dict:
    """Run the full OAuth 2.0 authorization code flow."""
    auth_code = None

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            qs = parse_qs(urlparse(self.path).query)
            auth_code = qs.get("code", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authorized!</h1>"
                b"<p>You can close this tab.</p></body></html>"
            )

        def log_message(self, format, *args):
            pass  # suppress server logs

    server = HTTPServer(("localhost", CALLBACK_PORT), CallbackHandler)

    authorize_url = (
        f"{BASE_URL}/approve_app"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={CALLBACK_URL}"
    )
    print("Opening browser for FreeAgent authorization...")
    webbrowser.open(authorize_url)
    server.handle_request()
    server.server_close()

    if not auth_code:
        raise SystemExit("Authorization failed: no code received.")

    resp = requests.post(
        f"{BASE_URL}/token_endpoint",
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": CALLBACK_URL,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    resp.raise_for_status()
    return _save_tokens(resp.json())


def _refresh_token(refresh_token: str) -> dict | None:
    """Attempt to refresh the access token. Returns None on failure."""
    try:
        resp = requests.post(
            f"{BASE_URL}/token_endpoint",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(CLIENT_ID, CLIENT_SECRET),
        )
        resp.raise_for_status()
        return _save_tokens(resp.json())
    except requests.RequestException:
        return None
