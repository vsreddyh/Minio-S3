# Backend (FastAPI)

FastAPI service for image ingestion, listing, and health reporting. MongoDB
stores metadata, MinIO is the hot store, AWS S3 is the cold mirror, and Redis
caches presigned URLs.

## Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

The API expects MongoDB, MinIO, and Redis to be reachable. AWS credentials are
optional: without them the S3 fallback and nightly mirror are disabled, but the
service still starts and `/health` reports the missing pieces.

Configuration is read from the environment (see `../.env.example`):
`MONGO_URI`, `MONGO_DB`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`,
`MINIO_SECRET_KEY`, `MINIO_BUCKET`, `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET`, `REDIS_URL`.

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

The tests mock MongoDB/MinIO/S3/Redis, so they do not need Docker or any
running services.
