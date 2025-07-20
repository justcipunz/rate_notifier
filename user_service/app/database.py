import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Получаем строку подключения из переменной окружения, которую мы задали в docker-compose.yml
DATABASE_URL = os.getenv("DATABASE_URL")

# Создаем асинхронный "движок" для SQLAlchemy
engine = create_async_engine(DATABASE_URL)

# Создаем класс для асинхронной сессии
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# Базовый класс для наших моделей таблиц
Base = declarative_base()

# Зависимость (dependency) для FastAPI, которая будет предоставлять сессию в эндпоинты
async def get_db_session():
    async with SessionLocal() as session:
        yield session
