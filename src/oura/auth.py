import http.server
import json
import os
import urllib.parse
import webbrowser
from pathlib import Path

import httpx

CONFIG_DIR = Path.home() / ".config" / "oura"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"

AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"

REDIRECT_PORT = 8976
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

SCOPES = [
    "email",
    "personal",
    "daily",
    "heartrate",
    "workout",
    "tag",
    "session",
    "spo2Daily",
]


def load_env() -> tuple[str, str]:
    """Load CLIENT_ID and CLIENT_SECRET from environment or .env file."""
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    if client_id and client_secret:
        return client_id, client_secret

    for env_path in [Path(".env"), Path(__file__).resolve().parents[3] / ".env"]:
        if not env_path.exists():
            continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip()
                if key == "CLIENT_ID":
                    client_id = value
                elif key == "CLIENT_SECRET":
                    client_secret = value
        break

    if not client_id or not client_secret:
        raise RuntimeError(
            "CLIENT_ID and CLIENT_SECRET must be set in environment or .env file"
        )
    return client_id, client_secret


def save_credentials(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(json.dumps(data, indent=2))


def load_credentials() -> dict | None:
    if not CREDENTIALS_FILE.exists():
        return None
    return json.loads(CREDENTIALS_FILE.read_text())


def get_access_token() -> str | None:
    # Check environment / .env first
    token = os.environ.get("OURA_ACCESS_TOKEN")
    if not token:
        for env_path in [Path(".env"), Path(__file__).resolve().parents[3] / ".env"]:
            if not env_path.exists():
                continue
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    if key.strip() == "OURA_ACCESS_TOKEN":
                        token = value.strip()
            break
    if token:
        return token

    creds = load_credentials()
    if creds and "access_token" in creds:
        return creds["access_token"]
    return None


def set_token(token: str) -> None:
    """Save a Personal Access Token directly."""
    save_credentials({"access_token": token})


def authorize() -> str:
    """Run the OAuth2 authorization code flow."""
    client_id, client_secret = load_env()

    auth_code = None

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if "code" in params:
                auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<h1>Authorized!</h1><p>You can close this window.</p>"
                )
            else:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                error = params.get("error", ["unknown"])[0]
                self.wfile.write(
                    f"<h1>Authorization failed</h1><p>{error}</p>".encode()
                )

        def log_message(self, format, *args):
            pass

    params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
        }
    )
    url = f"{AUTH_URL}?{params}"

    print(f"Opening browser for authorization...")
    print(f"If the browser doesn't open, visit:\n{url}\n")
    webbrowser.open(url)

    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), CallbackHandler)
    server.handle_request()

    if not auth_code:
        raise RuntimeError("Failed to get authorization code")

    print("Exchanging code for tokens...")
    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    response.raise_for_status()
    tokens = response.json()

    save_credentials(tokens)
    print("Authentication successful! Credentials saved.")
    return tokens["access_token"]


def refresh_access_token() -> str:
    """Refresh the access token using the stored refresh token."""
    creds = load_credentials()
    if not creds or "refresh_token" not in creds:
        raise RuntimeError("No refresh token available. Run 'oura auth' first.")

    client_id, client_secret = load_env()

    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": creds["refresh_token"],
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    response.raise_for_status()
    tokens = response.json()

    save_credentials(tokens)
    return tokens["access_token"]
