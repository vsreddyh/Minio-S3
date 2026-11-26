# MinIO-S3 — Cost-Optimized Image Ingestion Pipeline

Uploads hit self-hosted MinIO for fast, bursty ingest; a nightly cron mirrors
curated files to AWS S3 and purges MinIO. Reads go through short-lived presigned
URLs cached in Redis. Metadata lives in MongoDB.

## Architecture

```
React (Bun/Vite) ──► FastAPI :8000 ──┬──► MinIO (hot ingest)
                                     ├──► MongoDB (image index)
                                     ├──► Redis (cached signed URLs, 55 min TTL)
                                     └──► AWS S3 (nightly mirror, cold store)
```

- `POST /images/upload` stores bytes in MinIO (uuid-hex object names) + metadata
  in MongoDB (`backend/app/main.py`). The MinIO bucket is created automatically
  on the first upload.
- `GET /images` resolves each image to a presigned URL: Redis → MinIO (1h URL)
  → S3 fallback, then caches in Redis. There is no pagination: every document is
  returned. `object_url` is `null` when an object exists in neither store, and
  that does not fail the rest of the listing.
- `GET /images/file/{name}` streams the object bytes from MinIO only (404 when
  the object is missing).
- `GET /health` pings all four backing services. Overall status is `degraded`
  (HTTP 503) whenever any service reports `error`; when every service is
  `healthy`/`unavailable`, Mongo decides between `healthy` and `degraded`.
- Nightly sync (`backend/cronjob.sh`, midnight cron in the backend image): the
  entrypoint persists the container environment to `/etc/minio-sync.env`,
  the job recreates the `mc` aliases, runs `mc mirror --overwrite` MinIO → S3,
  deletes mirrored objects, and invalidates `signedurl:<obj>` in Redis.

## Run (Docker Compose)

```bash
cp .env.example .env   # fill in credentials
docker compose up --build
```

Both app services have `build:` sections, so `--build` builds `backend/` and
`frontend/` from this checkout (and tags the prebuilt image names). The frontend
API base is a build arg, not a runtime variable, because Vite inlines `VITE_*`
values into the static bundle:

```bash
VITE_API_BASE_URL=http://localhost:8000 docker compose build frontend
```

Use a browser-reachable URL (the default `http://localhost:8000`), not the
compose-internal `backend:8000` hostname.

Services: `frontend`, `backend` (`vsreddyh/minios3backend`), `mongo:noble`,
`redis:latest`, `minio/minio:latest` — see `docker-compose.yml`.
The backend needs AWS credentials + MinIO/S3 bucket env (see `.env.example`).

## Run backend locally

```bash
cd backend && python -m venv .venv && .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --port 8000   # needs MinIO + MongoDB + Redis running
```

## Tests

```bash
cd backend && .venv/bin/activate
pytest -q
```

The tests mock the backing services and do not require Docker.

## Known limitations

- No auth, delete endpoint, or pagination yet.
- MongoDB, MinIO, S3, and Redis clients silently degrade to `None` when they are
  unreachable; the API still starts and `/health` shows which service is down.
- The frontend shows a broken image if `object_url` is `null` (object not yet
  mirrored or already purged).
