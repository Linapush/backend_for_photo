from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from webapp.models.meta import DEFAULT_SCHEMA, Base


class User(Base):
    __tablename__ = 'user'
    __table_args__ = {'schema': DEFAULT_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)  # это автоинкрементируемый id записи в БД
    username: Mapped[int] = mapped_column(BigInteger, unique=True)  # это user_id из телегарм (изначально в учебном проекте так было)
    code: Mapped[str] = mapped_column(String)
