import secrets
from datetime import datetime
from models import BroadcastTaskModel, BroadcastTaskResultModel, ActiveSessionModel
from sqlalchemy import func, and_, Integer
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

    def create_broadcast_task(self, db: Session):
        op_symbol, op_func, op_name = random.choice(self.operations)
        a, b = self._generate_numbers(op_symbol)
        content = f"{op_name} {a} and {b}"

        task = BroadcastTaskModel(
            content=content,
            a=a,
            b=b,
            operation=op_symbol,
            expected_result=float(op_func(a, b))
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return {
            "task_id": task.id,
            "content": content,
            "a": a,
            "b": b,
            "operation": op_symbol
        }

    def get_latest_broadcast_task(self, db: Session):
        task = db.query(BroadcastTaskModel).order_by(BroadcastTaskModel.created_at.desc()).first()
        if not task:
            return None

        return {
            "task_id": task.id,
            "content": task.content,
            "a": task.a,
            "b": task.b,
            "operation": task.operation
        }

    def validate_broadcast_task_result(self, task_id: int, result: float, username: str, db: Session):
        task = db.query(BroadcastTaskModel).filter(BroadcastTaskModel.id == task_id).first()
        if not task:
            return {"status": "Task not found"}

        existing_result = (
            db.query(BroadcastTaskResultModel)
            .filter(
                BroadcastTaskResultModel.broadcast_task_id == task_id,
                BroadcastTaskResultModel.username == username
            )
            .first()
        )

        if existing_result:
            return {"status": "Task already submitted"}

        is_correct = abs(result - task.expected_result) < 0.0001
        task_result = BroadcastTaskResultModel(
            broadcast_task_id=task_id,
            username=username,
            answer=result,
            is_correct=is_correct
        )

        db.add(task_result)
        db.commit()

        return {
            "status": "Result submitted successfully",
            "is_correct": is_correct,
            "task_id": task_id
        }

    def get_broadcast_tasks_history(self, db: Session):
        # Query to get task details with result counts
        tasks = db.query(
            BroadcastTaskModel.id,
            BroadcastTaskModel.content,
            BroadcastTaskModel.a,
            BroadcastTaskModel.b,
            BroadcastTaskModel.operation,
            BroadcastTaskModel.expected_result,
            BroadcastTaskModel.created_at,
            func.count(BroadcastTaskResultModel.id).label('total_submissions'),
            func.sum(func.cast(BroadcastTaskResultModel.is_correct, Integer)).label('correct_count'),
            func.sum(func.cast(BroadcastTaskResultModel.is_correct == False, Integer)).label('incorrect_count')
        ).outerjoin(
            BroadcastTaskResultModel,
            BroadcastTaskModel.id == BroadcastTaskResultModel.broadcast_task_id
        ).group_by(BroadcastTaskModel.id).order_by(BroadcastTaskModel.created_at.desc()).all()

        # Format the results
        history = []
        for task in tasks:
            history.append({
                "id": task.id,
                "content": task.content,
                "a": task.a,
                "b": task.b,
                "operation": task.operation,
                "expected_result": task.expected_result,
                "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "total_submissions": task.total_submissions,
                "correct_count": task.correct_count or 0,
                "incorrect_count": task.incorrect_count or 0,
                "accuracy": round((task.correct_count or 0) / max(task.total_submissions, 1) * 100, 2)
            })

        return history

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
