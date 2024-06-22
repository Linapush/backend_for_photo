from typing import List, Optional

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.models.sirius.file import File as SQLAFile


async def get_filtered_data(
    session: AsyncSession,
    user_id: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[int] | None:
    query = (               # создаем запрос, который извлекает год (year) из столбца upload_date модели SQLA (File)
        select(func.extract('year', SQLAFile.upload_date).label('year'))
        .where(SQLAFile.user_id == user_id) # фильруем записи по user_id
        .group_by('year')   #группируем результаты по году
    )
    if year is not None:    # если указан год (year), переопределяем запрос для извлечения месяца (month) и фильтрации по году
        query = (
            select(func.extract('month', SQLAFile.upload_date).label('month'))
            .where(SQLAFile.user_id == user_id, extract('year', SQLAFile.upload_date) == year)
            .group_by('month')
        )
    if month is not None:    # если указан месяц (month), переопределяем запрос для извлечения дня (day) и фильтрации по году и месяцу
        query = (
            select(func.extract('day', SQLAFile.upload_date).label('day'))
            .where(
                SQLAFile.user_id == user_id,
                extract('year', SQLAFile.upload_date) == year,
                extract('month', SQLAFile.upload_date) == month,
            )
            .group_by('day')
        )

    result = await session.execute(query) # выполняем запрос с помощью объекта сессии
    data = result.scalars().all() #возвращает список значений из запроса

    return data if data else None 

# возвращаем полученные данные (data), если они есть, в противном случае возвращаем None