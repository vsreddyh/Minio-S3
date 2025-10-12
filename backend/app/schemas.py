from datetime import datetime
from pydantic import BaseModel


class Image(BaseModel):
    name: str
    createdAt: datetime


class ImageOut(BaseModel):
    object_url: str
    name: str
    createdAt: datetime
