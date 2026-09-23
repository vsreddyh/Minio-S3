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
  in MongoDB (`backend/app/main.py`).
- `GET /images` resolves each image to a presigned URL: Redis → MinIO (1h URL)
  → S3 fallback, then caches in Redis.
- `GET /health` pings all four backing services (503 `degraded` unless Mongo
  is healthy).
- Nightly sync (`backend/cronjob.sh`, midnight cron in the backend image):
  `mc mirror --overwrite` MinIO → S3, delete mirrored objects, invalidate
  `signedurl:<obj>` in Redis.

## Run (Docker Compose)

```bash
docker compose up --build
```

Services: `frontend`, `backend` (`vsreddyh/minios3backend`), `mongo:noble`,
`redis:latest`, `minio/minio:latest` — see `docker-compose.yml`.
The backend needs AWS credentials + MinIO/S3 bucket env (see compose file).

## Run backend locally

```bash
cd backend && python -m venv .venv && .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000   # needs MinIO + MongoDB + Redis running
```

## Known limitations

- The containerized frontend calls the API at `http://localhost:8000` — set the
  API base explicitly for non-local deploys.
- No auth, delete endpoint, or pagination yet.
