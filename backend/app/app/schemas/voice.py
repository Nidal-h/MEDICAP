from typing import Optional
import base64

from pydantic import BaseModel, validator, ValidationError
from datetime import datetime

from .user_doctor import Doctor
from .user_patient import Patient

# Shared properties
class VoiceBase(BaseModel):
    pass
    


# Properties to receive on item creation
class VoiceCreateUpload(VoiceBase):
    voice_file_b64 : str
    filename : str
    doctor_id : int
    patient_id : int
    title: Optional[str] = None
    folder_id: Optional[str] = None
    remarque : Optional[str] = None

    @validator('voice_file_b64')
    def validator_voice_file_b64(cls, value):
        decoded_string = base64.b64encode(base64.b64decode(value))
        decoded_string = str(decoded_string, 'ascii', 'ignore')
        size_mb = (3*len(value)/4)/10**6
        if decoded_string != value:
            raise ValidationError('voice_file_b64 need to be a base64 string')
        if size_mb > 20:
            raise ValidationError('voice_file_b64 file size hsould not exceed 20mb')
        return value

class AudioFileVoice(BaseModel):
    voice_file_b64 : str

    @validator('voice_file_b64')
    def validator_voice_file_b64(cls, value):
        decoded_string = base64.b64encode(base64.b64decode(value))
        decoded_string = str(decoded_string, 'ascii', 'ignore')
        size_mb = (3*len(value)/4)/10**6
        if decoded_string != value:
            raise ValidationError('voice_file_b64 need to be a base64 string')
        if size_mb > 20:
            raise ValidationError('voice_file_b64 file size hsould not exceed 20mb')
        return value

class VoiceCreate(VoiceBase):
    path : str
    doctor_id : int
    patient_id : int
    title: Optional[str] = None
    remarque : Optional[str] = None


# Properties to receive on item update
class VoiceUpdate(VoiceBase):
    title: Optional[str] = None
    remarque : Optional[str] = None


# Properties shared by models stored in DB
class VoiceInDBBase(VoiceBase):
    id: int
    path : str
    doctor_id : int
    patient_id : int
    title: Optional[str]=None
    remarque: Optional[str]=None
    date_creation : datetime
    note_created : bool = False

    class Config:
        orm_mode = True

class VoiceInDBBaseReduced(VoiceBase):
    id: int
    patient_id : int
    doctor_id : int
    title: Optional[str]=None
    date_creation : datetime
    note_created : bool = False

    class Config:
        orm_mode = True

# Properties to return to client
class Voice(VoiceInDBBase):
    pass

class VoiceReduced(VoiceInDBBaseReduced):
    pass

# Properties properties stored in DB
class VoiceInDB(VoiceInDBBase):
    pass
