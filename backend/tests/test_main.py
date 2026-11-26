"""Lightweight tests that do not require MongoDB, MinIO, S3, or Redis."""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import main


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    def find(self, *args, **kwargs):
        return list(self.docs)


class FakeDB:
    def __init__(self, docs=None):
        self.images = FakeCollection(docs)

    def command(self, name):
        return {"ok": 1}


class FakeObject:
    def stream(self, chunk_size):
        yield b"image-bytes"

    def close(self):
        pass

    def release_conn(self):
        pass


class FakeMinio:
    def list_buckets(self):
        return []

    def stat_object(self, bucket, name):
        return SimpleNamespace(content_type="image/png")

    def get_object(self, bucket, name):
        return FakeObject()


class FakeS3:
    def list_buckets(self):
        return {}


class FakeRedis:
    def ping(self):
        return True


@pytest.fixture
def healthy_state():
    main.app.state.db = FakeDB()
    main.app.state.minio_client = FakeMinio()
    main.app.state.s3_client = FakeS3()
    main.app.state.redis = FakeRedis()
    yield
    main.app.state.db = None
    main.app.state.minio_client = None
    main.app.state.s3_client = None
    main.app.state.redis = None


def test_root():
    assert main.read_root() == {"message": "Hello from backend"}


def test_health_healthy(healthy_state):
    body = main.health_check()
    assert body["status"] == "healthy"
    assert body["services"]["mongodb"]["status"] == "healthy"


def test_health_degraded_when_a_service_errors(healthy_state):
    class BrokenRedis:
        def ping(self):
            raise RuntimeError("redis down")

    main.app.state.redis = BrokenRedis()
    with pytest.raises(HTTPException) as exc:
        main.health_check()

    assert exc.value.status_code == 503
    assert exc.value.detail["status"] == "degraded"
    assert exc.value.detail["services"]["redis"]["status"] == "error"


def test_get_image_file_streams_bytes(healthy_state):
    response = main.get_image_file("photo.png")
    assert response.media_type == "image/png"

    async def collect():
        return b"".join([chunk async for chunk in response.body_iterator])

    assert asyncio.run(collect()) == b"image-bytes"


def test_image_out_allows_missing_object_url():
    image = main.ImageOut(name="missing.png", createdAt="2026-01-01T00:00:00")
    assert image.object_url is None


def test_list_images_keeps_unresolvable_objects():
    main.app.state.db = FakeDB(
        [{"name": "missing.png", "createdAt": "2026-01-01T00:00:00"}]
    )
    main.app.state.minio_client = None
    main.app.state.s3_client = None
    main.app.state.redis = None

    docs = main.list_images()

    assert docs == [
        {
            "name": "missing.png",
            "createdAt": "2026-01-01T00:00:00",
            "object_url": None,
        }
    ]
