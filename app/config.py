import os


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.auth_token_secret = os.getenv(
            "AUTH_TOKEN_SECRET", "sharingbridge-dev-secret-change-me"
        ).strip()
        self.auth_token_issuer = os.getenv(
            "AUTH_TOKEN_ISSUER", "sharingbridge-user-service"
        ).strip()
        self.auth_token_audience = os.getenv(
            "AUTH_TOKEN_AUDIENCE", "sharingbridge-clients"
        ).strip()
        self.cloudinary_cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
        self.cloudinary_api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
        self.cloudinary_api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()
        self.cloudinary_url = os.getenv("CLOUDINARY_URL", "").strip()
        self.photo_upload_mock = env_bool("PHOTO_UPLOAD_MOCK", False)
        self.max_upload_bytes = int(os.getenv("PHOTO_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))

    @property
    def cloudinary_configured(self) -> bool:
        if self.photo_upload_mock:
            return True
        if self.cloudinary_url:
            return True
        return bool(
            self.cloudinary_cloud_name
            and self.cloudinary_api_key
            and self.cloudinary_api_secret
        )


settings = Settings()
