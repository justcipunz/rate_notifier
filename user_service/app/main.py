from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from . import models, schemas, crud, security
from .database import engine, Base, get_db_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> models.User:
    """
    Декодирует токен, валидирует его и возвращает пользователя из БД.
    Это наша главная "охранная" зависимость.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


# Эта функция будет вызвана при старте приложения
async def create_db_and_tables():
    async with engine.begin() as conn:
        # Удаляем таблицы (для удобства при перезапуске в разработке)
        # await conn.run_sync(Base.metadata.drop_all)
        # Создаем таблицы на основе моделей из models.py
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()

# Добавляем обработчик события "startup"
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()

@app.get("/", tags=["Default"])
def read_root():
    return {"Service": "User Service", "Status": "Running"}

@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_new_user(
    user: schemas.UserCreate, db: AsyncSession = Depends(get_db_session)
):
    """
    Создает нового пользователя в системе.
    """
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return await crud.create_user(db=db, user=user)


@app.post("/token", response_model=schemas.Token, tags=["Auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    # OAuth2 стандарт требует, чтобы поле называлось 'username',
    # но мы будем использовать его для email.
    user = await crud.get_user_by_email(db, email=form_data.username)

    # Проверяем, что пользователь существует и пароль верный
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен
    access_token = security.create_access_token(
        data={"sub": user.email}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/marks/", response_model=schemas.RateMark, status_code=status.HTTP_201_CREATED, tags=["Marks"])
async def create_mark_for_user(
    mark: schemas.RateMarkCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user)
):
    """
    Создает новую целевую отметку для текущего авторизованного пользователя.
    
    - **target_rate**: Целевой курс (число с плавающей точкой).
    - **condition**: Условие срабатывания, 'above' (Уведомить меня, когда курс станет выше **target_rate**) или 'below' (Уведомить меня, когда курс станет ниже **target_rate**). По умолчанию 'above'.
    """
    # В будущем здесь можно добавить логику (например, ограничить кол-во отметок на пользователя)
    return await crud.create_user_mark(db=db, mark=mark, user_id=current_user.id)


@app.get("/marks/", response_model=list[schemas.RateMark], tags=["Marks"])
async def read_user_marks(
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user)
):
    """
    Возвращает список всех целевых отметок текущего авторизованного пользователя.
    """
    return await crud.get_user_marks(db=db, user_id=current_user.id)


@app.delete("/marks/{mark_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Marks"])
async def delete_mark(
    mark_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user)
):
    """
    Удаляет целевую отметку по ее ID.
    """
    deleted_mark = await crud.delete_user_mark(
        db=db, mark_id=mark_id, user_id=current_user.id
    )
    
    # Если функция crud вернула None, значит отметка не найдена
    # или не принадлежит текущему пользователю.
    if deleted_mark is None:
        raise HTTPException(status_code=404, detail="Mark not found")

    # В случае успеха ничего не возвращаем, так как статус 204 No Content
    return


@app.get("/users/me/", response_model=schemas.User, tags=["Users"])
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """
    Возвращает данные о текущем авторизованном пользователе.
    """
    return current_user