from fastapi import FastAPI
from . import models
from .database import engine, Base

# Эта функция будет вызвана при старте приложения
async def create_db_and_tables():
    async with engine.begin() as conn:
        # Удаляем таблицы (для удобства при перезапуске в разработке)
        # В продакшене так делать не стоит!
        await conn.run_sync(Base.metadata.drop_all)
        # Создаем таблицы на основе моделей из models.py
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()

# Добавляем обработчик события "startup"
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

# Создадим тестовый эндпоинт, чтобы проверить, что сервис работает
@app.get("/")
def read_root():
    return {"Service": "User Service", "Status": "Running"}
