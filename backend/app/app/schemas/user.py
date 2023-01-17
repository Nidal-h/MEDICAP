from typing import Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator, ValidationError
from uuid import uuid4, UUID
import base64
import io

# Shared properties
class Role(str, Enum):
    doctor = "doctor"
    patient = "patient"
    manager = "manager"
    assistant = "assistant"
    admin = "admin"
    
    def __str__(self):
        return str(self.value)
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    birth_date : Optional[datetime] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    role : Role
    profile_bs64: Optional[str] = """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"""
    

    @validator('profile_bs64')
    def validator_profile_bs64(cls, value):
        default_value = """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"""
        
        if value is "" or value is None:
            value = default_value
            return value
        decoded_string = base64.b64encode(base64.b64decode(value))
        decoded_string = str(decoded_string, 'ascii', 'ignore')
        size_mb = (3*len(value)/4)/10**6
        if decoded_string != value:
            raise ValidationError('profile_bs64 need to be a base64 string')
        if size_mb > 1:
            raise ValidationError('profile_bs64 file size should not exceed 1mb')
        return value


# Properties to receive via API on creation
class UserCreate(UserBase):
    uuid: UUID = Field(default_factory=uuid4)
    email: EmailStr
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None
    role : Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None
    uuid: Optional[UUID]
    firebase_device_token : Optional[str]=None

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
