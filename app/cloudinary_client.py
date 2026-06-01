from __future__ import annotations

import uuid
from typing import Any

import cloudinary
import cloudinary.uploader

from .config import settings


ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}


def _configure_cloudinary() -> None:
    if settings.cloudinary_url:
        cloudinary.config(cloudinary_url=settings.cloudinary_url, secure=True)
        return
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def thumbnail_url_for(public_id: str) -> str:
    _configure_cloudinary()
    return cloudinary.CloudinaryImage(public_id).build_url(
        transformation=[{"width": 200, "height": 200, "crop": "limit", "quality": "auto"}]
    )


def upload_reference_photo(
    *,
    user_id: str,
    file_bytes: bytes,
    mime_type: str,
) -> dict[str, Any]:
    if mime_type not in ALLOWED_MIME:
        raise ValueError("Only JPEG, PNG, or WebP images are allowed.")

    if settings.photo_upload_mock:
        artifact_suffix = uuid.uuid4().hex[:12]
        public_id = f"sharingbridge/mock/reference/{user_id}/{artifact_suffix}"
        view_url = f"https://res.cloudinary.com/demo/image/upload/{public_id}.jpg"
        thumb_url = f"{view_url}?w=200&h=200&c=limit"
        return {
            "cloudinary_public_id": public_id,
            "view_url": view_url,
            "thumbnail_url": thumb_url,
        }

    if not settings.cloudinary_configured:
        raise RuntimeError("Cloudinary is not configured.")

    _configure_cloudinary()
    folder = f"sharingbridge/reference/{user_id}"
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        resource_type="image",
        overwrite=False,
        unique_filename=True,
    )
    public_id = result.get("public_id") or ""
    secure_url = result.get("secure_url") or ""
    if not public_id or not secure_url:
        raise RuntimeError("Cloudinary upload did not return public_id and secure_url.")
    return {
        "cloudinary_public_id": public_id,
        "view_url": secure_url,
        "thumbnail_url": thumbnail_url_for(public_id),
    }
