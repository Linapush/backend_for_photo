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
from webapp.schema.file.file import File as FileSchema
from starlette.responses import Response


async def upload_file_to_minio(file: UploadFile, user_id: int) -> str:
    logger.info(f"Загрузка файла в Минио для пользователя {user_id}")
    bucket_name = f'user-{user_id}'

    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    current_date = date.today().strftime('%Y-%m-%d')
    file_path = f'{current_date}/{file.filename}'
    file.file.seek(0)

    try:
        # проверка file_content
        file_content = await file.read()
        if not file_content:
            logger.error("file_content пустой!")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка загрузки файла")

        logger.info(f"Размер file_content: {len(file_content)}")
        logger.info(f"Размер файла: {file.file.tell()}")

        file.file.seek(0)  

        await asyncio.get_event_loop().run_in_executor(
            None,
            minio_client.put_object,
            bucket_name,
            file_path,
            file.file,
            #file.file.tell(),
            len(file_content),  
            file.content_type,
        )
        logger.info(f"Файл загружен в Минио: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Ошибка загрузки файла в Минио: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


async def create_file(
        session: AsyncSession,
        file_data: FileCreate,
        # file: UploadFile,
        # user_id: int,
) -> File:
    logger.debug("Создание нового файла в базе")

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
    logger.info("Файл создан")
    return File.model_validate(new_file)


async def get_file_bytes(bucket_name: str, file_path: str) -> bytes:
    filename = file_path
    file_bytes = minio_client.get_object(bucket_name, filename)
    # file_bytes = file_object.read()
    # return file_bytes
    return Response(content=file_bytes)

    # file_bytes = minio_client.get_object(bucket_name, filename)
    # return file_bytes.read()
    #return Response(content=file_bytes)


async def get_filtered_files(
        session: AsyncSession,
        user_id: int,
        bucket_name: str,
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
    # file_schemas = [FileSchema.from_orm(file) for file in files]
    # return [
    #     {
    #         'file_info': file_schema.dict(),
    #         'file_bytes': (await get_file_bytes(bucket_name, file_schema.file_path))
    #     } for file_schema in file_schemas
    # ]


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

