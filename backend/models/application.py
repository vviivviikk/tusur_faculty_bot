# backend/models/application.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from backend.models.base import Base


class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    faculty_code = Column(String(20), nullable=False)
    status = Column(String(50), default='Подана')
    created_at = Column(DateTime, server_default=func.now())