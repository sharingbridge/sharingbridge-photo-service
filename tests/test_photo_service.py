import base64
import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from app.jwt_verify import JwtError, verify_auth_token
from app.main import app

client = TestClient(app)


def _mint_token(user_id: str, role: str = "donor") -> str:
    secret = "sharingbridge-dev-secret-change-me"
    issuer = "sharingbridge-user-service"
    audience = "sharingbridge-clients"
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "role": role,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + 3600,
    }

    def b64url(data: dict) -> str:
        raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    encoded_header = b64url(header)
    encoded_payload = b64url(payload)
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = base64.urlsafe_b64encode(
        hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    ).decode("utf-8").rstrip("=")
    return f"{encoded_header}.{encoded_payload}.{signature}"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["service"] == "photo-service"
    assert "config" in body
    assert "log_level" in body["config"]


def test_verify_auth_token_roundtrip():
    token = _mint_token("donor-1")
    payload = verify_auth_token(
        token,
        secret="sharingbridge-dev-secret-change-me",
        issuer="sharingbridge-user-service",
        audience="sharingbridge-clients",
    )
    assert payload["sub"] == "donor-1"
    assert payload["role"] == "donor"


def test_verify_auth_token_rejects_garbage():
    try:
        verify_auth_token(
            "not-a-jwt",
            secret="sharingbridge-dev-secret-change-me",
            issuer="sharingbridge-user-service",
            audience="sharingbridge-clients",
        )
        assert False, "expected JwtError"
    except JwtError:
        pass


def test_upload_requires_auth():
    response = client.post(
        "/v1/photos/upload",
        files={"file": ("ref.jpg", b"\xff\xd8\xff", "image/jpeg")},
        data={"photo_type": "seeker_reference"},
    )
    assert response.status_code == 401


def test_upload_rejects_coordinator():
    token = _mint_token("coord-1", role="coordinator")
    response = client.post(
        "/v1/photos/upload",
        headers={"authorization": f"Bearer {token}"},
        files={"file": ("ref.jpg", b"\xff\xd8\xff", "image/jpeg")},
        data={"photo_type": "seeker_reference"},
    )
    assert response.status_code == 403
