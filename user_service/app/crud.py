from sqlalchemy.orm import Session
from sqlalchemy import select

from . import models, schemas, security

async def get_user_by_email(db: Session, email: str) -> models.User | None:
    query = select(models.User).where(models.User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

async def create_user_mark(db: Session, mark: schemas.RateMarkCreate, user_id: int) -> models.RateMark:
    """Создает новую отметку для пользователя в БД."""
    db_mark = models.RateMark(
        target_rate=mark.target_rate,
        condition=mark.condition,
        user_id=user_id
    )
    db.add(db_mark)
    await db.commit()
    await db.refresh(db_mark)
    return db_mark

async def get_user_marks(db: Session, user_id: int) -> list[models.RateMark]:
    """Получает все отметки конкретного пользователя из БД."""
    query = select(models.RateMark).where(models.RateMark.user_id == user_id)
    result = await db.execute(query)
    # Используем .scalars().all() для получения списка всех результатов
    return result.scalars().all()

async def delete_user_mark(db: Session, mark_id: int, user_id: int) -> models.RateMark | None:
    """
    Удаляет отметку пользователя из БД.

    Возвращает удаленный объект, если он был найден и принадлежал пользователю,
    иначе возвращает None.
    """
    # Сначала найдем отметку, чтобы убедиться, что она существует и принадлежит пользователю
    query = select(models.RateMark).where(
        models.RateMark.id == mark_id,
        models.RateMark.user_id == user_id
    )
    result = await db.execute(query)
    mark_to_delete = result.scalar_one_or_none()

    # Если отметка найдена и принадлежит пользователю
    if mark_to_delete:
        await db.delete(mark_to_delete)
        await db.commit()
    
    return mark_to_delete
