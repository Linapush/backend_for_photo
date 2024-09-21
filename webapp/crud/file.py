import asyncio
from datetime import date
from typing import List, Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from webapp.db.minio import minio_client
from webapp.logger import logger
from webapp.models.sirius.file import File as SQLAFile
from webapp.schema.file.file import File, FileCreate, FileDownload


# # выгрузка файла в хранилище MinIO
async def upload_file_to_minio(file: UploadFile, user_id: int) -> str:
    logger.debug(f"Uploading file to Minio for user {user_id}")
    bucket_name = f'user-{user_id}'

    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    current_date = date.today().strftime('%Y-%m-%d')
    file_path = f'{current_date}/{file.filename}'
    file.file.seek(0)

    try:
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


# # создание объекта файла в базе данных
async def create_file(
        session: AsyncSession,
        file_data: FileCreate,
        # file: UploadFile,
        # user_id: int,
) -> File:
    logger.debug("Creating a new file")
    # minio_path = await upload_file_to_minio(file=file, user_id=user_id)
    # new_file = SQLAFile(*file_data.model_dump(), file_path=minio_path, user_id=user_id)
    # new_file = SQLAFile(*file_data.model_dump(), user_id=user_id)

    new_file = SQLAFile(
        user_id=file_data.user_id,
        file_path=file_data.file_path,
        file_name=file_data.file_name,
        file_type=file_data.file_type,
        file_size=file_data.file_size,
        upload_date=file_data.upload_date
    )

    session.add(new_file)
    await session.commit()
    await session.refresh(new_file)
    logger.info("New file created")
    return File.model_validate(new_file)


# # ф-ция для скачивание файла
# async def download_file_by_user_id_and_file_id(
#         session: AsyncSession, user_id: int, file_id: int) -> FileDownload | None:
#     result = await session.execute(select(SQLAFile).where(SQLAFile.user_id == user_id, SQLAFile.id == file_id))
#     file = result.scalars().first()
#     return FileDownload.model_validate(file) if file else None

async def download_file_by_user_id_and_file_id(
        session: AsyncSession, user_id: int, file_id: int
) -> FileDownload | None:
    result = await session.execute(select(SQLAFile).where(SQLAFile.user_id == user_id, SQLAFile.id == file_id))
    file = result.scalars().first()
    return FileDownload.model_validate(file) if file else None


# async def download_file_by_user_id_and_file_path(
#         user_id: int, file_path: str
# ) -> Dict | None:
#     bucket_name = f'user-{user_id}'

#     try:
#         file_info = minio_client.stat_object(bucket_name, file_path)
#         file_data = {
#             'file_name': file_path.split('/')[-1],
#             'file_type': file_info.content_type,
#             'file_size': file_info.size,
#             'file_path': file_path,
#             'user_id': user_id,
#         }
#         return file_data
#     except Exception as e:
#         logger.error(f"Error getting file details from MinIO: {e}")
#         return None


async def get_filtered_files(
        session: AsyncSession,
        user_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
        file_id: Optional[int] = None,
        file_name: Optional[str] = None
) -> List[SQLAFile] | None:
    query = select(SQLAFile).where(SQLAFile.user_id == user_id)

    if year is not None:
        query = query.where(extract('year', SQLAFile.upload_date) == year)

    if month is not None:
        try:
            month = int(month)
            query = query.where(extract('month', SQLAFile.upload_date) == month)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Некорректный формат месяца. Он должен быть целым числом."
            )

    if day is not None:
        try:
            day = int(day)
            query = query.where(extract('day', SQLAFile.upload_date) == day)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Некорректный формат дня. Он должен быть целым числом."
            )

    if year is not None and month is not None and day is not None:
        query = query.where(
            extract('year', SQLAFile.upload_date) == year,
            extract('month', SQLAFile.upload_date) == month,
            extract('day', SQLAFile.upload_date) == day
        )

    if file_id is not None:
        query = query.where(SQLAFile.id == file_id)
    if file_name is not None:
        query = query.where(SQLAFile.file_name == file_name)

    try:
        result = await session.execute(query)
        files = result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при выполнении запроса к базе данных: {e}"
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файлы из базы не найдены для указанных параметров."
        )

    return files

# # фильтр по дате
# async def get_filtered_files(
#         session: AsyncSession,
#         user_id: int,
#         year: Optional[int] = None,
#         month: Optional[int] = None,
#         day: Optional[int] = None,
#         file_id: Optional[int] = None,
#         file_name: Optional[str] = None
# ) -> List[File] | None:
#     query = select(SQLAFile, func.to_char(SQLAFile.upload_date, '%Y-%m-%d').label('upload_date_formatted')).where(SQLAFile.user_id == user_id)

#     if year is not None:
#         query = query.where(extract('year', SQLAFile.upload_date) == year)
#     if month is not None:
#         query = query.where(extract('month', SQLAFile.upload_date) == month)
#     if day is not None:
#         query = query.where(extract('day', SQLAFile.upload_date) == day)


#     try:
#         result = await session.execute(query)
#         files = result.scalars().all() # здесь list
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
#             detail=f"Ошибка при выполнении запроса к базе данных: {e}"
#         )

#     if not files:
#            raise HTTPException(
#                status_code=status.HTTP_404_NOT_FOUND,
#                detail="Файлы из базы не найдены для указанных параметров."
#            )

#     return files 


# старая версия
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
