from typing import Optional, Union

from pydantic import BaseModel
from datetime import datetime


# Shared properties
class RemarqueNoteBase(BaseModel):
    remarque : Optional[str] = None
    


class RemarqueNoteUpdate(BaseModel):
    seen : bool

# Properties to receive on item creation
class RemarqueNoteCreate(RemarqueNoteBase):
    note_id : int
    creator_id : int
    
    

# Properties shared by models stored in DB
class RemarqueNoteInDBBase(RemarqueNoteBase):
    id: int
    note_id : int
    seen : bool
    creator_id : int
    date_creation : datetime
    remarque : str

    class Config:
        orm_mode = True


# Properties to return to client
class RemarqueNote(RemarqueNoteInDBBase):
    pass


# Properties properties stored in DB
class RemarqueNoteInDB(RemarqueNoteInDBBase):
    pass
