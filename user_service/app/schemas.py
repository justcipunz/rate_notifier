from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

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
    condition: str = "above"  

class RateMarkCreate(RateMarkBase):
    pass

class RateMark(RateMarkBase):
    id: int
    is_active: bool
    user_id: int

    class Config:
        orm_mode = True