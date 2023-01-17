from typing import Optional, Union

from pydantic import BaseModel
from datetime import datetime

from .user_assistant import Assistant
from .voice import Voice

from uuid import UUID


# Shared properties
class NotificationToken(BaseModel):
    notification_user_id : UUID
    token: str