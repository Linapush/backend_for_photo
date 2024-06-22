from typing import List, Optional
from urllib.parse import quote

from fastapi import Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from minio.error import S3Error
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from webapp.api.file.router import file_router
from webapp.crud.file import create_file, download_file_by_user_id_and_file_id, get_filtered_files, upload_file_to_minio
from webapp.db.minio import minio_client
from webapp.db.postgres import get_session
from webapp.schema.file.file import File as FileSchema, FileCreate
from webapp.utils.auth.jwt import JwtTokenT, jwt_auth

# загружаем файл в минио, пользователь отправляет файл на endpoint /upload.
# создаем объект файла, сохраняем его в базе данных и загружаем файл в хранилище MinIO, возвращаем созданный объект файла.
@file_router.post('/upload', status_code=status.HTTP_201_CREATED, response_model=FileSchema, tags=['file'])
async def upload_file(
    file: UploadFile = File(...),                 # ожидаем файл, передаваемый в теле запроса
    session: AsyncSession = Depends(get_session), # используем Dependency Injection для получения объекта сессии
    access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
):
    try:
        file_data = FileCreate(
            file_name=file.filename,
            file_type=file.content_type,
            file_size=len(await file.read()),
        )
        # в create_file еще происходит upload_file_to_minio
        return await create_file(session=session, file_data=file_data, file=file, user_id=access_token['user_id'])
    except S3Error as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# посмотреть все загруженные фото в разрезе месяца и потом дня
# возвращаем отсортированные файлы
@file_router.get('/file', response_model=List[FileSchema], tags=['file'])
async def get_filtered_files_endpoint(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
    access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
):
    try:
        files = await get_filtered_files(
            session=session, user_id=access_token['user_id'], year=year, month=month, day=day
        )

        if files is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='Файлы не найдены для указанных параметров.'
            )

        return files
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# загружаем (скачиваем) файл по id (исп. также user_id)
@file_router.get('/download/{file_id}', response_class=StreamingResponse, tags=['file'])
async def download_file_endpoint(
    file_id: int,
    session: AsyncSession = Depends(get_session),
    access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
):
    try:
        file_record = await download_file_by_user_id_and_file_id(
            session=session, user_id=access_token['user_id'], file_id=file_id
        )
        if not file_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Файл не найден')

        response = minio_client.get_object(f'user-{access_token["user_id"]}', file_record.file_path)
        safe_filename = quote(file_record.file_name) # кодирует имя файла для безопасного использования в заголовках
        headers = {'Content-Disposition': f'attachment; filename*=utf-8""{safe_filename}'}
        return StreamingResponse(                    # тип ответа, который  позволяет  потоково  передавать  большие  файлы
            response.stream(32 * 1024),
            media_type=file_record.file_type,
            headers=headers,
        )
    except S3Error as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Ошибка хранилища: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))