# models.py
from sqlalchemy import ForeignKey, Column, Integer, String, DateTime
from datetime import datetime
from db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    sent_tasks = Column(Integer)
    public_key = Column(String)


class ActiveSession(Base):
    __tablename__ = "active_sessions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    ip_address = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class DBTask(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DBResult(Base):
    __tablename__ = "task_results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    answer = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
