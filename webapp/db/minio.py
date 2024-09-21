from conf.config import settings
from minio import Minio

minio_client = Minio(
    f'{settings.MINIO_HOST}:{settings.MINIO_PORT}',
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)
