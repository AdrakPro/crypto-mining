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

    async def send_message(self, message: Message, security_manager, current_user: str, db: Session):
        if message.to_user == current_user:
            raise HTTPException(
                status_code=400, 
                detail="Cannot send message to yourself"
            )

        if message.to_user not in security_manager.user_public_keys:
            raise HTTPException(
                status_code=404, 
                detail="Recipient not available"
            )
        encrypted = security_manager.encrypt_response(
                {"message": message.content, "from": current_user}, message.to_user, db
        )

        if DEBUG_MODE:
            print(f"Odszyfrowana wiadomość dla {message.to_user}: {message.content}")
            print(f"Odszyfrowana wiadomość dla {message.to_user}: {encrypted}")

        if message.to_user not in self.user_inboxes:
            self.user_inboxes[message.to_user] = []

        self.user_inboxes[message.to_user].append(encrypted)
        return {"status": "message stored"}

    async def get_message(self, user: str):
        if user not in self.user_inboxes or not self.user_inboxes[user]:
            return {"message": None}
        return self.user_inboxes[user].pop(0)
