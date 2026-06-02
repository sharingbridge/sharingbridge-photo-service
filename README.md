# sharingbridge-photo-service

Python (FastAPI) service for **reference photo upload** to Cloudinary and artifact metadata in Postgres.

## Endpoints

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | — |
| POST | `/v1/photos/upload` | Bearer JWT (donor) |
| GET | `/v1/photos/{artifact_id}` | Bearer JWT (donor owner or coordinator) |

## Configuration

See [env.example](./env.example) (copy to `.env` locally; `.env*` is gitignored). Use the same `AUTH_TOKEN_SECRET` / issuer / audience as `sharingbridge-user-service`.

For local dev without Cloudinary: `PHOTO_UPLOAD_MOCK=true`.

## Run

Requires **Python 3.10+** (3.13 works). Use a project venv; **do not** use Anaconda’s default `python` (often 3.7).

```powershell
cd sharingbridge-photo-service
python3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy env.example .env
# Edit .env (see env.example), then:
python -m pytest -q
uvicorn app.main:app --reload --port 8092
```

On Windows, `python` may still point at Anaconda — always use `python3.13` or the venv’s `.\.venv\Scripts\python.exe`.

Docker: see [Dockerfile](./Dockerfile) (port `8092`).

## Deploy (Render)

Root **`render.yaml`** — **New +** → **Blueprint** → this repo → set `AUTH_TOKEN_SECRET` and `DATABASE_URL` (same as user-service). Leave **Start Command** blank. Enable **Auto-Deploy on commit** to `main`.

| Variable | Notes |
|----------|--------|
| `PHOTO_UPLOAD_MOCK` | `true` until Cloudinary is configured |
| `CLOUDINARY_*` | Optional for real uploads |

Guide: [configuration/backend-render.md](https://github.com/sharingbridge/sharingbridge/blob/main/configuration/backend-render.md).

Setup guide: [configuration/photo-service-local.md](https://github.com/sharingbridge/sharingbridge/blob/main/configuration/photo-service-local.md) in the main repo.

## Tests

```powershell
pytest -q
```

## Roadmap

- On-server image processing (resize, privacy blur) before upload
- `delivery_acknowledgement` photo type and match scoring
