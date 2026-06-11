from __future__ import annotations

try:
    from typing import Annotated
except ImportError:  # Python < 3.9
    from typing_extensions import Annotated  # type: ignore

from fastapi import Depends, Header, HTTPException

from .config import settings
from .jwt_verify import JwtError, verify_auth_token


def _read_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.strip().lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail={"code": "missing_auth_context", "message": "A valid Bearer token is required."},
        )
    return authorization.strip()[7:].strip()


def get_auth_payload(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    token = _read_bearer(authorization)
    try:
        return verify_auth_token(
            token,
            secret=settings.auth_token_secret,
            issuer=settings.auth_token_issuer,
            audience=settings.auth_token_audience,
        )
    except JwtError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_token", "message": str(exc)},
        ) from exc


def is_initiator_role(role: str | None) -> bool:
    return role in {"initiator", "donor"}


def require_donor(
    payload: Annotated[dict, Depends(get_auth_payload)],
) -> dict:
    if not is_initiator_role(payload.get("role")):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "forbidden",
                "message": "This action requires an initiator account.",
            },
        )
    return payload


def require_donor_or_coordinator(
    payload: Annotated[dict, Depends(get_auth_payload)],
) -> dict:
    role = payload.get("role")
    if not is_initiator_role(role) and role != "coordinator":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "forbidden",
                "message": "This action requires an initiator or coordinator account.",
            },
        )
    return payload
