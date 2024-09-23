from datetime import date
from io import BytesIO
from typing import List, Optional, Any, Dict
from urllib.parse import quote

from fastapi import Depends, File, HTTPException, UploadFile, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse, ORJSONResponse
from minio.error import S3Error
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from webapp.api.file.router import file_router
from webapp.crud.file import create_file
from webapp.crud.file import download_file_by_user_id_and_file_id, get_filtered_files
from webapp.crud.file import upload_file_to_minio
from webapp.db.minio import minio_client
from webapp.db.postgres import get_session
from webapp.logger import logger
from webapp.schema.file.file import File as FileSchema, FileCreate
from webapp.utils.auth.jwt import JwtTokenT, jwt_auth


@file_router.post(
    '/upload',
    status_code=status.HTTP_201_CREATED,
    tags=['file']
)
async def upload_file(
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_session),
        access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
):
    try:
        logger.info(f"Received a file upload request{file, session, access_token}")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизованы")

        file_content = await file.read()
        file_path = await upload_file_to_minio(file=file, user_id=access_token['user_id'])

        file_data = {
            'user_id': access_token['user_id'],
            'file_name': file.filename,
            'file_path': file_path,
            'file_type': file.content_type,
            'file_size': len(file_content),
            'upload_date': date.today(),
        }
        # file.file.seek(0)
        # new_file = await create_file(session, FileCreate(**file_data), file, access_token['user_id'])
        new_file = await create_file(session, FileCreate(
            user_id=file_data['user_id'],
            file_name=file_data['file_name'],
            file_path=file_data['file_path'],
            file_type=file_data['file_type'],
            file_size=file_data['file_size'],
            upload_date=file_data['upload_date']
        ))

        logger.info(f'Создан объект в памяти {new_file}')

        return ORJSONResponse(content=jsonable_encoder(file_data), status_code=status.HTTP_201_CREATED)
    except S3Error as e:
        logger.error(f"S3Error occurred: {e.message}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка сервера при работе с хранилищем")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный запрос.")


# @file_router.get('/file/', response_model=List[Dict[str, Any]], tags=['file']) 
@file_router.get('/file/', response_model=List[FileSchema], tags=['file'])   
async def get_filtered_files_endpoint(
        year: Optional[int] = Query(None, description="Year"),
        month: Optional[int] = Query(None, description="Month"),
        day: Optional[int] = Query(None, description="Day"),
        file_id: Optional[int] = Query(None, description="File ID"),
        file_name: Optional[str] = Query(None, description="File Name"),
        session: AsyncSession = Depends(get_session),
        access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
):
    try:
        returned_files = await get_filtered_files(
            bucket_name = f'user-{access_token["user_id"]}',
            session=session,
            user_id=access_token['user_id'],
            year=year,
            month=month,
            day=day,
            file_id=file_id,
            file_name=file_name
        )
        file_schemas = [FileSchema.from_orm(file) for file in returned_files]
        logger.info(f"Переданный файлы: {file_schemas}")
        return file_schemas
        # return returned_files
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


#########################################################################################################################################
# @file_router.get('/download/{file_id}', response_class=StreamingResponse, tags=['file'])
# async def download_file_endpoint(
#     file_id: int,
#     session: AsyncSession = Depends(get_session),
#     access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
# ):
#     try: # получаем запись файла из базы данных
#         file_record = await download_file_by_user_id_and_file_id(
#             session=session, user_id=access_token['user_id'], file_id=file_id
#         )
#         if not file_record:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Файл не найден')
#         # получаем объект из MinIO
#         response = minio_client.get_object(f'user-{access_token["user_id"]}', file_record.file_path)
#         safe_filename = quote(file_record.file_name)            # кодируем имя файла для безопасного использования в заголовках
#         headers = {'Content-Disposition': f'attachment; filename"{safe_filename}'}
#         return StreamingResponse(                               # тип ответа, который  позволяет  потоково  передавать  большие  файлы
#             response.stream(32 * 1024),
#             media_type=file_record.file_type,
#             headers=headers,
#         )
#     except S3Error as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Ошибка хранилища: {str(e)}')
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#########################################################################################################################################


@file_router.get('/download/{file_id}', tags=['file'])
async def download_file_endpoint(
        file_id: int,
        session: AsyncSession = Depends(get_session),
        access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
):
    bucket_name = f'user-{access_token["user_id"]}'

    try:
        file_record = await download_file_by_user_id_and_file_id(
            session=session, user_id=access_token['user_id'], file_id=file_id
        )

        if not file_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Файл не найден')

        # logger.info(f"Попытка получить объект из MinIO: bucket={bucket_name}, path={file_record.file_path}")

        response = minio_client.get_object(bucket_name, file_record.file_path)
        # logger.info(f"Объект успешно получен: bucket={bucket_name}, path={file_record.file_path}")

        data = BytesIO(response.read())
        response.close()
        response.release_conn()

        safe_filename = quote(file_record.file_name)
        headers = {'Content-Disposition': f'attachment; filename="{safe_filename}"'}

        return StreamingResponse(data, media_type=file_record.file_type, headers=headers)

    except S3Error as e:
        logger.error(f"Ошибка при доступе к MinIO: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Ошибка хранилища: {str(e)}')
    except Exception as e:
        logger.error(f"Общая ошибка: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# @file_router.get(
#         '/download/{file_id}', 
#         response_class=StreamingResponse, 
#         tags=['file']
#         )
# async def download_file_endpoint(
#         file_id: int,
#         session: AsyncSession = Depends(get_session),
#         access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
# ):
#     try:
#         file_record = await download_file_by_user_id_and_file_id(
#             session=session, user_id=access_token['user_id'], file_id=file_id
#         )
#         if not file_record:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Файл не найден')

#         response = minio_client.get_object(f'user-{access_token["user_id"]}', file_record.file_path)
#         safe_filename = quote(file_record.file_name)  # кодирует имя файла для безопасного использования в заголовках
#         headers = {'Content-Disposition': f'attachment; filename*=utf-8""{safe_filename}'}
#         return StreamingResponse(  # тип ответа, который  позволяет  потоково  передавать  большие  файлы
#             response.stream(32 * 1024),
#             media_type=file_record.file_type,
#             headers=headers,
#         )
#     except S3Error as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
#             detail=f'Ошибка хранилища: {str(e)}')
#     except Exception as e:
#         raise HTTPException(
#         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         detail=f'Не удалось скачать файл: {str(e)}'
#         )


# # версия /upload в базу и minio
# @file_router.post('/upload', status_code=status.HTTP_201_CREATED, response_model=FileSchema, tags=['file'])
# async def upload_file(
#     file: UploadFile = File(...),
#     session: AsyncSession = Depends(get_session),
#     access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
# ):
#     try:
#         file_data = FileCreate(
#             file_name=file.filename,
#             file_type=file.content_type,
#             file_size=len(await file.read()),
#         )
#         # в create_file еще происходит upload_file_to_minio
#         return await create_file(session=session, file_data=file_data, file=file, user_id=access_token['user_id'])
#     except S3Error as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# версия /file/ напрямую в минио
# async def get_user_id_from_minio(file_name: str):

#     try:
#         minio_object = minio_client.get_object('my-bucket', file_name)

#         metadata = minio_object.metadata
#         user_id = int(metadata['user_id'])

#         return user_id
#     except Exception as e:
#         logger.error(f"Ошибка получения user_id из MinIO: {e}")
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка получения user_id из MinIO.")

# @file_router.post(
#     '/file/{year}/{month}/{day}',
#     status_code=status.HTTP_200_OK,
#     tags=['file']
# )
# async def get_filtered_files_endpoint(
#         year: int,
#         month: int,
#         day: int,
#         user_id: int = Depends(get_user_id_from_minio),
# ) -> dict:
#     bucket_name = f'user-{user_id}'
#     logger.info(bucket_name)

#     logger.info(f"Запрос на получение файлов для пользователя {user_id}")
#     logger.info(f"Параметры запроса: year={year}, month={month}, day={day}")

#     try:
#         buckets = minio_client.list_buckets()
#         if bucket_name not in [b.name for b in buckets]:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Бакета {bucket_name} не существует.")

#         prefix = f'user-{user_id}/{year}-{month}-{day}'

#         objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
#         for obj in objects:
#             file_path = obj.object_name
#             file_date = (datetime.strptime(file_path.split('/')[0], '%Y-%m-%d'))

#             if year is not None and file_date.year != year:
#                 continue
#             if month is not None and file_date.month != month:
#                 continue
#             if day is not None and file_date.day != day:
#                 continue

#             file_url = minio_client.presigned_get_object(bucket_name, file_path, expires=3600)
#             file_url = file_data["file_url"]
#             file_info = minio_client.stat_object(bucket_name, file_path)
#             file_data = {
#                 "file_name": file_path.split('/')[-1],
#                 "file_type": file_info.content_type,
#                 "file_size": file_info.size,
#                 "file_path": file_path,
#                 "user_id": user_id,
#                 "file_url": file_url,
#                 "file_id": obj.etag,
#             }
#             return file_data
#         return None

#     except S3Error as e:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# # версия /download из минио
# @file_router.get('/download/{file_path}', response_class=StreamingResponse, tags=['file'])
# async def download_file_endpoint(
#         file_path: str,
#         access_token: JwtTokenT = Depends(jwt_auth.get_current_user),
# ):
#     try:
#         file_record = await download_file_by_user_id_and_file_path(
#             user_id=access_token['user_id'], file_path=file_path
#         )
#         if not file_record:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Файл не найден')

#         response = minio_client.get_object(f'user-{access_token["user_id"]}', file_record['file_path'])
#         safe_filename = quote(file_record['file_name'])  # кодирует имя файла для безопасного использования в заголовках
#         headers = {'Content-Disposition': f'attachment; filename*=utf-8""{safe_filename}'}
#         return StreamingResponse(  # тип ответа, который  позволяет  потоково  передавать  большие  файлы
#             response.stream(32 * 1024),
#             media_type=file_record['file_type'],
#             headers=headers,
#         )
#     except S3Error as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Ошибка хранилища: {str(e)}')
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail=f'Не удалось скачать файл: {str(e)}')
