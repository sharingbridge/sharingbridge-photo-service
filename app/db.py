from __future__ import annotations

import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .config import settings


def new_artifact_id() -> str:
    return f"pa-{uuid.uuid4()}"


@contextmanager
def get_connection():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required.")
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn


def ensure_schema(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS photo_artifacts (
          artifact_id TEXT PRIMARY KEY,
          user_id TEXT NOT NULL,
          photo_type TEXT NOT NULL,
          cloudinary_public_id TEXT NOT NULL,
          view_url TEXT NOT NULL,
          thumbnail_url TEXT NOT NULL,
          mime_type TEXT,
          file_size INTEGER,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    conn.commit()


def insert_artifact(
    conn,
    *,
    artifact_id: str,
    user_id: str,
    photo_type: str,
    cloudinary_public_id: str,
    view_url: str,
    thumbnail_url: str,
    mime_type: str | None,
    file_size: int | None,
) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT INTO photo_artifacts (
          artifact_id, user_id, photo_type, cloudinary_public_id,
          view_url, thumbnail_url, mime_type, file_size, created_at
        ) VALUES (
          %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            artifact_id,
            user_id,
            photo_type,
            cloudinary_public_id,
            view_url,
            thumbnail_url,
            mime_type,
            file_size,
            created_at,
        ),
    )
    conn.commit()
    return {
        "artifact_id": artifact_id,
        "user_id": user_id,
        "photo_type": photo_type,
        "cloudinary_public_id": cloudinary_public_id,
        "view_url": view_url,
        "thumbnail_url": thumbnail_url,
        "mime_type": mime_type,
        "file_size": file_size,
        "created_at": created_at.isoformat(),
    }


def fetch_artifact(conn, artifact_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT artifact_id, user_id, photo_type, cloudinary_public_id,
               view_url, thumbnail_url, mime_type, file_size, created_at
        FROM photo_artifacts
        WHERE artifact_id = %s
        """,
        (artifact_id,),
    ).fetchone()
    if not row:
        return None
    created = row["created_at"]
    if isinstance(created, datetime):
        created = created.astimezone(timezone.utc).isoformat()
    return {
        "artifact_id": row["artifact_id"],
        "user_id": row["user_id"],
        "photo_type": row["photo_type"],
        "cloudinary_public_id": row["cloudinary_public_id"],
        "view_url": row["view_url"],
        "thumbnail_url": row["thumbnail_url"],
        "mime_type": row["mime_type"],
        "file_size": row["file_size"],
        "created_at": str(created),
    }
