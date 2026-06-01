from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


class JwtError(Exception):
    pass


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def verify_auth_token(
    token: str,
    *,
    secret: str,
    issuer: str,
    audience: str,
) -> dict[str, Any]:
    if not token or not token.strip():
        raise JwtError("Token is required.")
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise JwtError("Token format is invalid.")
    encoded_header, encoded_payload, encoded_signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_sig = hmac.new(
        secret.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    given_sig = _b64url_decode(encoded_signature)
    if not hmac.compare_digest(given_sig, expected_sig):
        raise JwtError("Token signature is invalid.")
    payload = json.loads(_b64url_decode(encoded_payload))
    now = int(time.time())
    if payload.get("iss") != issuer:
        raise JwtError("Token issuer is invalid.")
    if payload.get("aud") != audience:
        raise JwtError("Token audience is invalid.")
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp <= now:
        raise JwtError("Token is expired.")
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise JwtError("Token subject is invalid.")
    role = payload.get("role")
    if not isinstance(role, str) or not role.strip():
        raise JwtError("Token role is invalid.")
    return payload
