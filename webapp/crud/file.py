import asyncio
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import UploadFile, HTTPException
# from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from webapp.logger import logger

from webapp.db.minio import minio_client
from webapp.crud.user import get_user
from webapp.models.sirius.file import File as SQLAFile
from webapp.schema.file.file import File, FileCreate, FileDownload


# 4 выгрузка файла в хранилище MinIO
# создаем бакет (если его нет), определяем путь к файлу, сохраняем файл в MinIO и возвращаем путь к загруженному файлу
async def upload_file_to_minio(file: UploadFile, user_id: int) -> str:
    logger.debug(f"Uploading file to Minio for user {user_id}")
    bucket_name = f'user-{user_id}'

    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    current_date = datetime.now().strftime('%Y-%m-%d')
    file_path = f'{current_date}/{file.filename}'
    # возвращает текущую позицию указателя в файле
    # file_size = file.file.tell()
    # перемещает указатель в начало файла
    file.file.seek(0)

    try:  #
        await asyncio.get_event_loop().run_in_executor(
            None,
            minio_client.put_object,
            bucket_name,
            file_path,
            file.file,
            file.file.tell(),
            file.content_type,
        )
        logger.info(f"File uploaded to Minio: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error uploading file to Minio: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# # 1 создание объекта файла в базе данных.
# # вызываем функцию upload_file_to_minio, чтобы загрузить файл в MinIO,
# # затем создаем объект файла в базе данных, сохраняем его и возвращаем созданный объект файла
async def create_file(
    session: AsyncSession,
    file_data: FileCreate,
    file: UploadFile,
    user_id: int,
) -> File:
    logger.debug("Creating a new file")
    minio_path = await upload_file_to_minio(file=file, user_id=user_id)
    new_file = SQLAFile(*file_data.model_dump(), file_path=minio_path, user_id=user_id)
    session.add(new_file)
    await session.commit()
    await session.refresh(new_file)
    logger.info("New file created")
    return File.model_validate(new_file)


# # 3 ф-ция для скачивание файла
# async def download_file_by_user_id_and_file_id(
#         session: AsyncSession, user_id: int, file_id: int) -> FileDownload | None:
#     result = await session.execute(select(SQLAFile).where(SQLAFile.user_id == user_id, SQLAFile.id == file_id))
#     file = result.scalars().first()
#     return FileDownload.model_validate(file) if file else None

async def download_file_by_user_id_and_file_path(
        user_id: int, file_path: str
) -> Dict | None:
    bucket_name = f'user-{user_id}'

    try:
        file_info = minio_client.stat_object(bucket_name, file_path)
        file_data = {
            'file_name': file_path.split('/')[-1],
            'file_type': file_info.content_type,
            'file_size': file_info.size,
            'file_path': file_path,
            'user_id': user_id,
        }
        return file_data
    except Exception as e:
        logger.error(f"Error getting file details from MinIO: {e}")
        return None  # Return None if the file is not found

# # 2 фильтр по годам, месяцам и дням
# async def get_filtered_files(
#         session: AsyncSession,
#         user_id: int,
#         year: Optional[int] = None,
#         month: Optional[int] = None,
#         day: Optional[int] = None,
# ) -> List[File] | None:
#     query = select(SQLAFile)

#     query = query.where(SQLAFile.user_id == user_id)

#     if year is not None:
#         query = query.where(extract('year', SQLAFile.upload_date) == year)
#     # условие, чтобы значение года в поле upload_date совпадало с указанным годом

#         if month is not None:
#             query = query.where(extract('month', SQLAFile.upload_date) == month)

#             if day is not None:
#                 query = query.where(extract('day', SQLAFile.upload_date) == day)

#     query = query.order_by(SQLAFile.upload_date)

#     result = await session.execute(query)
#     files = result.scalars().all()
#     return [File.model_validate(file) for file in files] if files else None
#     # валидация и преобразование данных в объект типа File
#     # возвращаем список объекта типа файл

# #4 выгрузка файла в хранилище MinIO.
# создаем бакет (если его нет), определяем путь к файлу, сохраняем файл в MinIO и возвращаем путь к загруженному файлу
# async def upload_file_to_minio(file: UploadFile, user_id: int) -> str:
#     bucket_name = f'user-{user_id}' # бакет 'user-user_id'

#     if not minio_client.bucket_exists(bucket_name):
#         minio_client.make_bucket(bucket_name) # создаем бакет

#     current_date = datetime.now().strftime('%Y-%m-%d')
#     file_path = f'{current_date}/{file.filename}'
#     file_size = file.file.tell()
# возвращает текущую позицию указателя в файле относительно его начала.
# Текущая позиция указателя — это позиция (количество байт), с которой будет осуществляться следующее чтение/запись
#     file.file.seek(0) # перемещает указатель в заданную позицию
# # получаем размер файла, используя метод tell() для текущей позиции указателя в файле,
# и перемещаем указатель в начало файла с помощью метода seek(0)

#     await asyncio.get_event_loop().run_in_executor(
#         None,
#         minio_client.put_object,
#         bucket_name,
#         file_path,
#         file.file,
#         file_size,
#         file.content_type,
#     )

#     return file_path

