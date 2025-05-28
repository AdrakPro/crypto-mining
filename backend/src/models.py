from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from db import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    sent_tasks = Column(Integer)
    public_key = Column(String)


class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskResultModel(Base):
    __tablename__ = "task_results"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    answer = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    is_correct = Column(Boolean)


class ActiveSessionModel(Base):
    __tablename__ = "active_sessions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    ip = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
