"""Materialize Streamlit secrets for the container at startup.

Streamlit only reads secrets from ``<cwd>/.streamlit/secrets.toml`` (it does not
read environment variables), while the platform delivers credentials through the
environment. This bridges the two: it writes the file into a runtime directory
outside the repo.

SUPABASE_URL / SUPABASE_KEY come from the environment when provided (real
credentials). When SUPABASE_KEY is absent it signs a local anonymous JWT for the
local PostgREST dev service with the shared PGRST_JWT_SECRET.
"""

import base64
import hashlib
import hmac
import json
import os
import pathlib

LOCAL_URL = "http://rest-proxy"
LOCAL_JWT_SECRET = "base44-local-postgrest-jwt-secret-0123456789"


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _local_anon_jwt(secret: str) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"role": "anon", "iss": "base44-local"}, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = _b64(hmac.new(secret.encode(), signing_input, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


url = os.environ.get("SUPABASE_URL", "").strip() or LOCAL_URL
key = os.environ.get("SUPABASE_KEY", "").strip()
if not key:
    key = _local_anon_jwt(os.environ.get("PGRST_JWT_SECRET", LOCAL_JWT_SECRET))
    print(f"[secrets] no SUPABASE_KEY set, using local dev anon key for {url}")

out = pathlib.Path.cwd() / ".streamlit" / "secrets.toml"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(
    f"SUPABASE_URL = {json.dumps(url)}\n"
    f"SUPABASE_KEY = {json.dumps(key)}\n"
)
print(f"[secrets] wrote {out}")
