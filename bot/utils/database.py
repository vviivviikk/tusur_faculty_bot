from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from bot.config import Config
from backend.models.base import Base
from backend.models.user import User

from backend.models.application import Application

engine = create_async_engine(Config.DATABASE_URL, echo=False, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

async def get_user_by_telegram_id(telegram_id):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

async def create_or_update_user(telegram_id, username, first_name, last_name):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user:
            return user
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        await session.commit()
        return user

async def add_application(user_id: int, faculty_code: str):
    async with async_session() as session:
        # Проверим нет ли уже заявки на этот факультет
        exists = await session.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.faculty_code == faculty_code
            )
        )
        if exists.scalar_one_or_none():
            return  # уже есть такая заявка
        app = Application(user_id=user_id, faculty_code=faculty_code)
        session.add(app)
        await session.commit()
        return app

async def get_applications_by_user_id(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Application).where(Application.user_id == user_id)
        )
        return result.scalars().all()

