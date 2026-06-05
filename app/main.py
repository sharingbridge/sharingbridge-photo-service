from __future__ import annotations

try:
    from typing import Annotated
except ImportError:  # Python < 3.9
    from typing_extensions import Annotated  # type: ignore

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from .auth import require_donor, require_donor_or_coordinator
from .cloudinary_client import ALLOWED_MIME, upload_reference_photo
from .config import settings
from .db import ensure_schema, fetch_artifact, get_connection, insert_artifact, new_artifact_id
from .service_log import configure_logging, log_startup_from_issues, resolve_log_level

logger = configure_logging("photo-service")

app = FastAPI(
    title="SharingBridge Photo Service",
    version="0.1.0",
    description="Reference photo upload and artifact metadata (Cloudinary).",
)

ALLOWED_PHOTO_TYPES = {"seeker_reference", "delivery_acknowledgement"}


def _public_config() -> dict:
    return {
        "service": "photo-service",
        "database_url_set": bool(settings.database_url),
        "cloudinary_configured": settings.cloudinary_configured,
        "auth_token_secret_set": bool(settings.auth_token_secret),
        "log_level": resolve_log_level(),
    }


def _startup_config_issues(config: dict) -> list[str]:
    issues: list[str] = []
    if not config.get("cloudinary_configured"):
        issues.append("Cloudinary is not configured")
    if not config.get("database_url_set"):
        issues.append("DATABASE_URL is unset (upload metadata will be unavailable)")
    return issues


@app.on_event("startup")
def startup() -> None:
    config = _public_config()
    log_startup_from_issues(logger, config, _startup_config_issues(config))
    settings.require_cloudinary()
    if not settings.database_url:
        return
    with get_connection() as conn:
        ensure_schema(conn)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "photo-service",
        "config": _public_config(),
    }


@app.post("/v1/photos/upload")
async def upload_photo(
    auth: Annotated[dict, Depends(require_donor)],
    file: UploadFile = File(...),
    photo_type: str = Form("seeker_reference"),
) -> dict:
    normalized_type = (photo_type or "").strip()
    if normalized_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_request",
                "message": "photo_type must be seeker_reference or delivery_acknowledgement.",
            },
        )

    if normalized_type != "seeker_reference":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "not_implemented",
                "message": "Only seeker_reference uploads are supported in this release.",
            },
        )

    if not settings.database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "storage_unavailable",
                "message": "DATABASE_URL is not configured.",
            },
        )

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_request",
                "message": "File must be JPEG, PNG, or WebP.",
            },
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_request", "message": "Uploaded file is empty."},
        )
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "file_too_large",
                "message": f"Image must be at most {settings.max_upload_bytes} bytes.",
            },
        )

    user_id = auth["sub"].strip()
    try:
        uploaded = upload_reference_photo(
            user_id=user_id,
            file_bytes=raw,
            mime_type=content_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_request", "message": str(exc)},
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "upload_failed", "message": str(exc)},
        ) from exc

    artifact_id = new_artifact_id()
    with get_connection() as conn:
        record = insert_artifact(
            conn,
            artifact_id=artifact_id,
            user_id=user_id,
            photo_type=normalized_type,
            cloudinary_public_id=uploaded["cloudinary_public_id"],
            view_url=uploaded["view_url"],
            thumbnail_url=uploaded["thumbnail_url"],
            mime_type=content_type,
            file_size=len(raw),
        )

    return {
        "artifact_id": record["artifact_id"],
        "photo_type": record["photo_type"],
        "view_url": record["view_url"],
        "thumbnail_url": record["thumbnail_url"],
        "created_at": record["created_at"],
    }


@app.get("/v1/photos/{artifact_id}")
def get_photo(
    artifact_id: str,
    auth: Annotated[dict, Depends(require_donor_or_coordinator)],
) -> dict:
    if not settings.database_url:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

    normalized_id = artifact_id.strip()
    with get_connection() as conn:
        record = fetch_artifact(conn, normalized_id)

    if not record:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Photo not found."})

    role = auth.get("role")
    user_id = auth["sub"].strip()
    if role == "donor" and record["user_id"] != user_id:
        raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Not your photo."})

    return record


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": "error", "message": str(exc.detail)},
    )
