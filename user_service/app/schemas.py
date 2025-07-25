from pydantic import BaseModel, EmailStr

# Схема для создания пользователя (что мы ждем в запросе)
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Схема для ответа (что мы возвращаем, без пароля!)
class User(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class RateMarkBase(BaseModel):
    target_rate: float
    condition: str = "above"  # Условие: "above" или "below"

class RateMarkCreate(RateMarkBase):
    pass

class RateMark(RateMarkBase):
    id: int
    is_active: bool
    user_id: int

    class Config:
        orm_mode = True