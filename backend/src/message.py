from fastapi import HTTPException
from typing import Dict, Optional
from schemas import Message

class MessageManager:
    def __init__(self):
        self.user_inboxes = {}

    def send_message(self, message: Message, security_manager) -> Dict[str, str]:
        if message.to_user not in security_manager.user_public_keys:
            raise HTTPException(status_code=404, detail="User not available")

        encrypted_msg = security_manager.encrypt_response(
            {"message": message.content},
            message.to_user
        )

        if message.to_user not in self.user_inboxes:
            self.user_inboxes[message.to_user] = []

        self.user_inboxes[message.to_user].append(encrypted_msg)
        return {"status": "message stored"}

    def get_message(self, user: str) -> Optional[Dict]:
        if user not in self.user_inboxes or not self.user_inboxes[user]:
            return {"message": None}
        return self.user_inboxes[user].pop(0)
