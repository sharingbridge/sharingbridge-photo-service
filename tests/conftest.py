import os

# Set before app.config loads so a developer's `.env` does not break unit tests.
os.environ.setdefault("AUTH_TOKEN_SECRET", "sharingbridge-dev-secret-change-me")
os.environ.setdefault("AUTH_TOKEN_ISSUER", "sharingbridge-user-service")
os.environ.setdefault("AUTH_TOKEN_AUDIENCE", "sharingbridge-clients")
os.environ.setdefault("PHOTO_UPLOAD_MOCK", "true")
