from fastapi import APIRouter

file_router = APIRouter(prefix='/file', tags=["file"])
filter_router = APIRouter(prefix='/filter')
