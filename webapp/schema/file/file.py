from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict
from pydantic import validator


class File(BaseModel):
    id: int
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    upload_date: datetime

    model_config = ConfigDict(from_attributes=True)


class FileSchemaWithURL(File):
    download_url: str


class FillQueue(BaseModel):
    user_ids: List[int]


class FileDownload(File):
    file_path: str
    file_type: str

    model_config = ConfigDict(from_attributes=True)


class FileCreate(BaseModel):
    user_id: int
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    upload_date: date

    @validator('user_id')
    def validate_user_id(cls, value):
        if value < 0:
            raise ValueError('User ID must be a positive integer')
        return value

    @validator('upload_date', pre=True, always=True)
    def set_upload_date(cls, value):
        return value

    @validator('file_path')
    def validate_file_path(cls, value, values):
        if values.get('file_type') == 'image/jpeg' and not value.endswith('.jpg'):
            raise ValueError('JPEG files must have a .jpg extension')
        return value


class Config:
    arbitrary_types_allowed = True
