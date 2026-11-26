from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Image(BaseModel):
    name: str
    createdAt: datetime


class ImageOut(BaseModel):
    # None when the object cannot be resolved in MinIO or S3; a single missing
    # object should not fail the whole listing.
    object_url: Optional[str] = None
    name: str
    createdAt: datetime
