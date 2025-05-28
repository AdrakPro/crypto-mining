import secrets
from typing import Dict, List
import time
from schemas import Result

class SessionManager:
    def __init__(self):
        self.tasks = {}
        self.active_sessions = []

    def get_or_create_task(self, user: str) -> Dict[str, int]:
        if user not in self.tasks:
            a = secrets.randbelow(100) + 1
            b = secrets.randbelow(100) + 1
            self.tasks[user] = {"a": a, "b": b, "expected_sum": a + b}
        return {"a": self.tasks[user]["a"], "b": self.tasks[user]["b"]}

    def validate_task_result(self, user: str, result: Result) -> Dict[str, any]:
        if user not in self.tasks:
            return {"status": "No active task"}

        expected = self.tasks[user]["expected_sum"]
        response = (
            {"status": "Correct"}
            if result.sum == expected
            else {"status": "Incorrect", "expected": expected, "received": result.sum}
        )
        del self.tasks[user]
        return response

    def add_session(self, username: str, ip: str):
        self.active_sessions.append({
            "username": username,
            "ip": ip,
            "timestamp": time.time()
        })

    def list_active_sessions(self) -> List[Dict[str, str]]:
        return [
            {
                "username": s["username"],
                "ip": s["ip"],
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(s["timestamp"]))
            }
            for s in self.active_sessions
        ]
