from sqlalchemy import Column, Integer, String, Boolean
from backend.models.base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone = Column(String(50))
    email = Column(String(120))
    role = Column(String(50), default='user')
    is_active = Column(Boolean, default=True)