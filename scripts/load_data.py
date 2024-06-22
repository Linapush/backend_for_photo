import json
import asyncio
import argparse
from pathlib import Path
from typing import List

from sqlalchemy import insert

from webapp.db.postgres import async_session
from webapp.models.meta import metadata

parser = argparse.ArgumentParser() # парсинг аргументов командной строки

parser.add_argument('fixtures', nargs='+', help='<Required> Set flag') # аргумент fixtures, который должен быть задан пользователем и принимает список файлов фикстур

args = parser.parse_args()         # парсятся аргументы командной строки

# 
async def main(fixtures: List[str]) -> None:
    for fixture in fixtures:
        fixture_path = Path(fixture)
        model = metadata.tables[fixture_path.stem]

        with open(fixture_path, 'r') as file:
            values = json.load(file)

        async with async_session() as session:
            await session.execute(insert(model).values(values))
            await session.commit()


if __name__ == '__main__':
    asyncio.run(main(args.fixtures))
