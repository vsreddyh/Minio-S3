from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from uuid import uuid4
import io
import boto3
from botocore.exceptions import ClientError
import redis

from .schemas import Image, ImageOut


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "minios3_db")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "newbucket")

# AWS S3 Configuration (fallback)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "minioands3")
# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# print(f"AWS S3 Config: {AWS_ACCESS_KEY_ID}, {AWS_REGION}, {AWS_S3_BUCKET}")

app = FastAPI(title="minios3 Backend - FastAPI")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",  # Alternative localhost
        "http://localhost:3000",  # React dev server alternative
        "http://127.0.0.1:3000",
        "*",  # Allow all origins
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# We'll store the client on app.state


@app.on_event("startup")
def startup_db_client():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        # force a server selection to fail fast if not available
        client.server_info()
        app.state.mongo_client = client
        app.state.db = client[DB_NAME]
    except ServerSelectionTimeoutError:
        # If Mongo isn't available, mark as None. No in-memory fallback.
        app.state.mongo_client = None
        app.state.db = None
    # initialize MinIO client
    try:
        mc = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
        # test connection by listing buckets (will raise on failure)
        mc.list_buckets()
        app.state.minio_client = mc
    except Exception:
        app.state.minio_client = None
    
    # initialize AWS S3 client (fallback)
    try:
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
            # test connection by listing buckets
            s3_client.list_buckets()
            app.state.s3_client = s3_client
        else:
            app.state.s3_client = None
    except Exception:
        app.state.s3_client = None

    # initialize Redis client (cache)
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        # ping to ensure connection
        r.ping()
        app.state.redis = r
    except Exception:
        app.state.redis = None


@app.on_event("shutdown")
def shutdown_db_client():
    client = getattr(app.state, "mongo_client", None)
    if client:
        client.close()


@app.get("/")
def read_root():
    return {"message": "Hello from backend"}


@app.get("/health")
def health_check():
    """Health check endpoint that returns the status of all services."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "mongodb": {"status": "unknown", "details": None},
            "minio": {"status": "unknown", "details": None},
            "aws_s3": {"status": "unknown", "details": None},
            "redis": {"status": "unknown", "details": None}
        }
    }
    
    # Check MongoDB
    try:
        if app.state.db is not None:
            # Try a simple operation to verify connection
            app.state.db.command("ping")
            health_status["services"]["mongodb"]["status"] = "healthy"
            health_status["services"]["mongodb"]["details"] = f"Connected to {DB_NAME}"
        else:
            health_status["services"]["mongodb"]["status"] = "unavailable"
            health_status["services"]["mongodb"]["details"] = "MongoDB client not initialized"
    except Exception as e:
        health_status["services"]["mongodb"]["status"] = "error"
        health_status["services"]["mongodb"]["details"] = str(e)
    
    # Check MinIO
    try:
        minio_client = getattr(app.state, "minio_client", None)
        if minio_client is not None:
            # Try to list buckets to verify connection
            minio_client.list_buckets()
            health_status["services"]["minio"]["status"] = "healthy"
            health_status["services"]["minio"]["details"] = f"Connected to {MINIO_ENDPOINT}"
        else:
            health_status["services"]["minio"]["status"] = "unavailable"
            health_status["services"]["minio"]["details"] = "MinIO client not initialized"
    except Exception as e:
        health_status["services"]["minio"]["status"] = "error"
        health_status["services"]["minio"]["details"] = str(e)
    
    # Check AWS S3
    try:
        s3_client = getattr(app.state, "s3_client", None)
        if s3_client is not None:
            # Try to list buckets to verify connection
            s3_client.list_buckets()
            health_status["services"]["aws_s3"]["status"] = "healthy"
            health_status["services"]["aws_s3"]["details"] = f"Connected to S3 in {AWS_REGION}"
        else:
            health_status["services"]["aws_s3"]["status"] = "unavailable"
            health_status["services"]["aws_s3"]["details"] = "AWS S3 client not initialized (credentials may be missing)"
    except Exception as e:
        health_status["services"]["aws_s3"]["status"] = "error"
        health_status["services"]["aws_s3"]["details"] = str(e)

    # Check Redis
    try:
        r = getattr(app.state, "redis", None)
        if r is not None:
            r.ping()
            health_status["services"]["redis"]["status"] = "healthy"
            health_status["services"]["redis"]["details"] = f"Connected to {REDIS_URL}"
        else:
            health_status["services"]["redis"]["status"] = "unavailable"
            health_status["services"]["redis"]["details"] = "Redis client not initialized"
    except Exception as e:
        health_status["services"]["redis"]["status"] = "error"
        health_status["services"]["redis"]["details"] = str(e)
    
    # Determine overall health status
    service_statuses = [service["status"] for service in health_status["services"].values()]
    
    if "error" in service_statuses:
        health_status["status"] = "degraded"
    elif all(status in ["healthy", "unavailable"] for status in service_statuses):
        # At least MongoDB should be healthy for basic functionality
        if health_status["services"]["mongodb"]["status"] == "healthy":
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "degraded"
    else:
        health_status["status"] = "degraded"
    
    # Return appropriate HTTP status code
    if health_status["status"] == "healthy":
        return health_status
    else:
        raise HTTPException(status_code=503, detail=health_status)


def _img_doc_to_schema(doc) -> Image:
    """Convert a MongoDB image document to the Image schema."""
    return Image(name=doc["name"], createdAt=doc["createdAt"]) 


@app.post("/images", response_model=Image)
def create_image(image: Image):
    """Create an image metadata record in MongoDB.

    Requires the database to be available. Returns the saved image data.
    """
    if app.state.db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    coll = app.state.db.images
    doc = {"name": image.name, "createdAt": image.createdAt}
    coll.insert_one(doc)
    return image


@app.get("/images", response_model=List[ImageOut])
def list_images():
    """Return all image metadata from MongoDB.

    Returns 503 if the database isn't available.
    """
    if app.state.db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    docs = list(app.state.db.images.find({}, {"_id": 0}))

    def cache_key(name: str) -> str:
        return f"signedurl:{name}"

    r = getattr(app.state, "redis", None)
    minio_client = getattr(app.state, "minio_client", None)
    s3_client = getattr(app.state, "s3_client", None)

    for d in docs:
        url = None
        key = cache_key(d['name'])
        # try cache first
        if r is not None:
            try:
                url = r.get(key)
            except Exception:
                url = None
        if url:
            d['object_url'] = url
            continue

        # compute signed URL
        try:
            object_exists_in_minio = False
            if minio_client:
                try:
                    minio_client.stat_object(MINIO_BUCKET, d['name'])
                    object_exists_in_minio = True
                except S3Error:
                    object_exists_in_minio = False

            if minio_client and object_exists_in_minio:
                url = minio_client.presigned_get_object(MINIO_BUCKET, d['name'], expires=timedelta(hours=1))
            elif s3_client:
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': AWS_S3_BUCKET, 'Key': f"minio/newbucket/{d['name']}"},
                    ExpiresIn=3600
                )
            else:
                url = None
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            url = None

        d['object_url'] = url
        # cache the result with TTL slightly less than signed URL expiry (e.g., 55 minutes)
        if r is not None and url:
            try:
                r.setex(key, 55 * 60, url)
            except Exception:
                pass

    print(docs)
    return docs

@app.post("/images/upload", response_model=dict)
async def upload_image(file: UploadFile = File(...), createdAt: str = Form(None)):
    """Upload a file to MinIO and persist metadata to MongoDB.

    - If MinIO and MongoDB are available, the file is stored in MinIO and the metadata saved to MongoDB.
    - If MinIO isn't available, returns 503. If Mongo isn't available, metadata is stored in memory.
    """
    """Upload a file to MinIO and store metadata in MongoDB.

    Preconditions:
    - MinIO client must be available (storage)
    - MongoDB must be available (metadata)

    Returns stored metadata including object URL.
    """
    minio_client = getattr(app.state, "minio_client", None)
    if minio_client is None:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": "Storage not available"})
    if app.state.db is None:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": "Database not available"})

    # create bucket if not exists
    try:
        found = minio_client.bucket_exists(MINIO_BUCKET)
        if not found:
            minio_client.make_bucket(MINIO_BUCKET)
    except S3Error as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": f"MinIO error: {e}"})

    # pick a safe object name
    ext = ''
    if "." in file.filename:
        ext = file.filename.split(".")[-1]
    obj_name = f"{uuid4().hex}.{ext}" if ext else uuid4().hex

    # read bytes and upload to MinIO
    body = await file.read()
    try:
        minio_client.put_object(MINIO_BUCKET, obj_name, data=io.BytesIO(body), length=len(body), content_type=file.content_type)
    except S3Error as e:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": f"MinIO upload failed: {e}"})

    created_dt = datetime.utcnow()

    # persist metadata in MongoDB and return result
    doc = {"name": obj_name, "createdAt": created_dt }
    app.state.db.images.insert_one(doc)
    return {"name": obj_name, "createdAt": created_dt.isoformat()}