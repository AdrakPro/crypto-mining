from fastapi import HTTPException
import os

from sqlalchemy.orm import Session

from schemas import Message
from dotenv import load_dotenv

load_dotenv()

DEBUG_MODE = os.getenv("DEBUG_MODE", "0") == "1"


class MessageManager:
    def __init__(self):
        self.user_inboxes = {}

    def send_message(self, message: Message, security_manager, db: Session):
        if message.to_user not in security_manager.user_public_keys:
            raise HTTPException(status_code=404, detail="User not available")

        encrypted = security_manager.encrypt_response(
            {"message": message.content}, message.to_user, db
        )

        if DEBUG_MODE:
            print(f"Odszyfrowana wiadomość dla {message.to_user}: {message.content}")
            print(f"Odszyfrowana wiadomość dla {message.to_user}: {encrypted}")

        if message.to_user not in self.user_inboxes:
            self.user_inboxes[message.to_user] = []

        self.user_inboxes[message.to_user].append(encrypted)
        return {"status": "message stored"}

    def get_message(self, user: str):
        if user not in self.user_inboxes or not self.user_inboxes[user]:
            return {"message": None}
        return self.user_inboxes[user].pop(0)
