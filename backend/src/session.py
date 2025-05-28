import secrets
from datetime import datetime
from models import TaskModel, TaskResultModel, ActiveSessionModel
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
import random


class SessionManager:
    def __init__(self):
        self.operations = [
            ("+", lambda x, y: x + y, "add"),
            ("-", lambda x, y: x - y, "subtract"),
            ("*", lambda x, y: x * y, "multiply"),
            ("/", lambda x, y: x / y, "divide"),
        ]

    @staticmethod
    def _generate_numbers(operation: str):
        if operation == "/":
            b = secrets.randbelow(9) + 1
            a = b * (secrets.randbelow(10) + 1)
            return a, b
        else:
            a = secrets.randbelow(100) + 1
            b = secrets.randbelow(100) + 1
            return a, b

    def create_task(self, username: str, db: Session):
        current_time = datetime.utcnow()
        op_symbol, op_func, op_name = random.choice(self.operations)

        a, b = self._generate_numbers(op_symbol)
        content = f"{op_name} {a} and {b}"

        task = TaskModel(
            content=content,
            created_at=current_time,
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        expected_result = op_func(a, b)
        if op_symbol == "/":
            expected_result = float(expected_result)

        return {
            "status": "Task created successfully",
            "task_id": task.id,
            "content": task.content,
            "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "created_by": username,
            "a": a,
            "b": b,
            "expected_result": expected_result,
        }

    def validate_task_result(self, task_id: int, result: int, username: str, db: Session):
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        current_time = datetime.utcnow()
        if not task:
            return {"status": "Task not found"}

        existing_result = (
            db.query(TaskResultModel)
            .filter(TaskResultModel.username == username, TaskResultModel.task_id == task_id)
            .first()
        )

        if existing_result:
            return {"status": "Task already submitted"}

        task_result = TaskResultModel(
            username=username,
            task_id=task_id,
            answer=result,
            submitted_at=current_time,
        )

        is_correct = abs(float(result) - expected_result) < 0.0001
        task_result.is_correct = is_correct

        db.add(task_result)
        db.commit()

        return {
            "status": "Result submitted successfully",
            "is_correct": is_correct,
            "task_id": task_id,
            "submitted_at": self.current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "username": username,
            "answer": result,
        }

    @staticmethod
    def list_active_sessions(db: Session):
        subquery = (
            db.query(
                ActiveSessionModel.username,
                func.max(ActiveSessionModel.timestamp).label(
                    "latest_timestamp")
            )
            .group_by(ActiveSessionModel.username)
            .subquery()
        )

        latest_sessions = (
            db.query(ActiveSessionModel)
            .join(
                subquery,
                and_(
                    ActiveSessionModel.username == subquery.c.username,
                    ActiveSessionModel.timestamp == subquery.c.latest_timestamp,
                )
            )
            .all()
        )

        print(latest_sessions)

        return latest_sessions
