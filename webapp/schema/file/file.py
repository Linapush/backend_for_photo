from pydantic import BaseModel, ConfigDict
from typing import List


class File(BaseModel):
    id: int
    file_name: str

    model_config = ConfigDict(from_attributes=True)

class FillQueue(BaseModel):
    user_ids: List[int]


class FileDownload(File):
    file_path: str
    file_type: str

    model_config = ConfigDict(from_attributes=True)


class FileCreate(BaseModel):
    file_name: str
    file_type: str
    file_size: int
