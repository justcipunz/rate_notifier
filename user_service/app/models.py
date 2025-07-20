from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    marks = relationship("RateMark", back_populates="owner")


class RateMark(Base):
    __tablename__ = "rate_marks"

    id = Column(Integer, primary_key=True, index=True)
    target_rate = Column(Float, nullable=False)
    # Условие может быть 'above' или 'below' (курс должен стать выше или ниже отметки)
    condition = Column(String, default="above") 
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="marks")

