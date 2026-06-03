import os

import pytest

# Set before app.config loads so a developer's `.env` does not break unit tests.
os.environ.setdefault("AUTH_TOKEN_SECRET", "sharingbridge-dev-secret-change-me")
os.environ.setdefault("AUTH_TOKEN_ISSUER", "sharingbridge-user-service")
os.environ.setdefault("AUTH_TOKEN_AUDIENCE", "sharingbridge-clients")
os.environ.setdefault("CLOUDINARY_CLOUD_NAME", "test-cloud")
os.environ.setdefault("CLOUDINARY_API_KEY", "test-key")
os.environ.setdefault("CLOUDINARY_API_SECRET", "test-secret")
os.environ.pop("PHOTO_UPLOAD_MOCK", None)


@pytest.fixture(autouse=True)
def mock_cloudinary_upload(monkeypatch):
    """Avoid real Cloudinary API calls in unit tests."""

    def fake_upload(_file_bytes, **kwargs):
        folder = kwargs.get("folder", "sharingbridge/reference/test")
        return {
            "public_id": f"{folder}/artifact-test",
            "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/view.jpg",
        }

    monkeypatch.setattr(
        "app.cloudinary_client.cloudinary.uploader.upload",
        fake_upload,
    )
    monkeypatch.setattr(
        "app.cloudinary_client.thumbnail_url_for",
        lambda _public_id: "https://res.cloudinary.com/test-cloud/image/upload/thumb.jpg",
    )
    monkeypatch.setattr(
        "app.cloudinary_client.cloudinary.config",
        lambda **_kwargs: None,
    )
