from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from datetime import datetime
from db import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    sent_tasks = Column(Integer)
    public_key = Column(String)


class ActiveSessionModel(Base):
    __tablename__ = "active_sessions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    ip = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class BroadcastTaskModel(Base):
    __tablename__ = "broadcast_tasks"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    a = Column(Integer)
    b = Column(Integer)
    operation = Column(String)
    expected_result = Column(Float)

class BroadcastTaskResultModel(Base):
    __tablename__ = "broadcast_task_results"
    id = Column(Integer, primary_key=True, index=True)
    broadcast_task_id = Column(Integer, ForeignKey("broadcast_tasks.id"))
    username = Column(String, nullable=False)
    answer = Column(Float, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    is_correct = Column(Boolean)
