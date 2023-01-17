from typing import Optional, Union, List, Tuple

from pydantic import BaseModel
from datetime import datetime

from .user_assistant import Assistant
from .voice import Voice
from .note import Note
from .user import User

class Search(BaseModel):
	voice_id: str
	doctor_id:int
	patient_id: int
	title: Optional[str]
	remarque: Optional[str]
	date_creation: datetime
	note_created: bool
	note_id: Optional[int]
	content_txt: Optional[str]
	validated: Optional[bool]
	assistant_id: Optional[int]
	modifier_id: Optional[int]
	note_date_modification: Optional[datetime]
	class Config:
		orm_mode = True