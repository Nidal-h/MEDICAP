import os
import aiofiles

from typing import Any, List, Optional, Union
from itertools import chain
from pathlib import Path


from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi import File, UploadFile, Form
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

import uuid
import base64

from datetime import datetime
from app import crud, models, schemas
from app.api import deps

from app.models.doctor_manager import DoctorManager
from app.models.assistant_manager import AssistantManager
from app.models.doctor_patient import DoctorPatient
from app.models.voice import Voice

from app.models.note import Note

from app.utils import send_notification, send_notification_firebase

router = APIRouter()


@router.get("/", response_model=List[schemas.Voice])
def read_voices(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve all voices. Only super user can use it
    """
    if crud.user.is_superuser(current_user):
        voices = crud.voice.get_all(db)
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return voices

 #to change after having the relationship crud
@router.get("/{voice_id}", response_model=schemas.VoiceReduced)

def read_voice_by_id(
    *,
    db: Session = Depends(deps.get_db),
    voice_id : int,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve voices. Only the doctor of the patient, the assistant owner of the voice or his manager can retrieve it
    """
     #to change after having the relationship crud
    voice = crud.voice.get_by_voice_id(db, id=voice_id)
    if voice:
        manager_idx = crud.user.get_doctor_managers(db=db, doctor_id=voice.doctor_id)
        manager_idx = list(chain(*manager_idx))
        assistant_idx = crud.user.get_doctor_assistants(db=db, doctor_id=voice.doctor_id)
        assistant_idx = list(chain(*assistant_idx))
        
        if voice.note_created:
            note = crud.note.get_by_voice_id(db=db, id=voice.id)
            if note:
                assistant_idx = [note.assistant_id]
        
        if current_user.id == voice.doctor_id:
            return voice
        elif current_user.id == voice.patient_id:
            return voice
        elif current_user.id in manager_idx:
            return voice
        elif current_user.id in assistant_idx:
            return voice
        else:
            raise HTTPException(status_code=400, detail="Not enough permissions")
    return voice

@router.get("/note/{voice_id}", response_model=schemas.Note)
def read_note_voice_by_id(
    *,
    db: Session = Depends(deps.get_db),
    voice_id : int,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve note of the voice. 
    Only the doctor of the patient, the assistant owner of the voice or his manager can retrieve it
    """
     #to change after having the relationship crud
    voice = crud.voice.get_by_voice_id(db, id=voice_id)
    if voice:
        manager_idx = crud.user.get_doctor_managers(db=db, doctor_id=voice.doctor_id)
        manager_idx = list(chain(*manager_idx))
        assistant_idx = crud.user.get_doctor_assistants(db=db, doctor_id=voice.doctor_id)
        assistant_idx = list(chain(*assistant_idx))
        
        if voice.note_created:
            note = crud.note.get_by_voice_id(db=db, id=voice.id)
            if note:
                assistant_idx = [note.assistant_id]
            else:
                raise HTTPException(status_code=404, detail="No note found for the voice_id")
        else:
            raise HTTPException(status_code=404, detail="No note created for the voice")
        
        if current_user.id == voice.doctor_id:
            return note
        elif current_user.id == voice.patient_id:
            return note
        elif current_user.id in manager_idx:
            return note
        elif current_user.id in assistant_idx:
            return note
        else:
            raise HTTPException(status_code=400, detail="Not enough permissions")
    else:
        raise HTTPException(status_code=400, detail="No Voice found with given voice_id")

@router.get("/audiofile/{voice_id}", response_model=schemas.AudioFileVoice)
def audiofile_by_id(
    *,
    db: Session = Depends(deps.get_db),
    voice_id : int,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve the audio voice by id. 
    Only the doctor of the patient, the assistant owner of the voice or his manager can retrieve it
    """
     #to change after having the relationship crud
    voice = crud.voice.get_by_voice_id(db, id=voice_id)
    if voice:
        audio_file = Path(voice.path)
        if not audio_file.is_file():
            raise HTTPException(status_code=500, detail="The audio file of the given voice not found, please check with your admin")
        
        #audio_file = FileResponse(path=voice.path, filename=voice.path.split('/')[-1], media_type='audio/mpeg')
        
        f = open(voice.path, 'rb')
        audio_file = base64.b64encode(f.read())
        audio_file = str(audio_file, 'ascii', 'ignore')
        f.close()

        audio_file = schemas.AudioFileVoice(voice_file_b64=audio_file)

        
        manager_idx = crud.user.get_doctor_managers(db=db, doctor_id=voice.doctor_id)
        manager_idx = list(chain(*manager_idx))
        assistant_idx = crud.user.get_doctor_assistants(db=db, doctor_id=voice.doctor_id)
        assistant_idx = list(chain(*assistant_idx))

        if not voice.note_created and current_user.role == 'assistant':
            raise HTTPException(status_code=400, detail="note need to be created to retrieve the voice by an assistant")

        if voice.note_created:
            note = crud.note.get_by_voice_id(db=db, id=voice.id)
            if note:
                assistant_idx = [note.assistant_id]
        if current_user.id == voice.doctor_id:
            return audio_file
        elif current_user.id == voice.patient_id:
            return audio_file
        elif current_user.id in manager_idx:
            return audio_file
        elif current_user.id in assistant_idx:
            return audio_file
        else:
            raise HTTPException(status_code=400, detail="Not enough permissions")
    else:
        raise HTTPException(status_code=404, detail="No voice found with this id")

@router.get("/doctor/{doctor_id}", response_model=Union[List[schemas.Voice], int])
def read_doctor_voices(
    *,
    db: Session = Depends(deps.get_db),
    doctor_id: int,
    skip: int=0,
    limit: int=5,
    note_created: Optional[bool]=None,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve voices related to a doctors. 
    Only That dctor and a super user can use it
    """
    if (crud.user.is_superuser(current_user) or (current_user.id  == doctor_id and current_user.role=='doctor')):
        if count:
            return crud.voice.get_multi_by_doctor_count(db=db, doctor_id=doctor_id, note_created=note_created)
        voices = crud.voice.get_multi_by_doctor_id(db, doctor_id=doctor_id, note_created=note_created, skip=skip, limit=limit)
    else :
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return voices

@router.get("/manager/{manager_id}", response_model=Union[List[schemas.VoiceReduced], int])
def read_manager_voices(
    *,
    db: Session = Depends(deps.get_db),
    manager_id: int,
    skip: int=0,
    limit: int=5,
    note_created: Optional[bool]=None,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve voices related to that manager.
    Only that manager and super user can use it
    """
    if (crud.user.is_superuser(current_user) or (current_user.id  == manager_id and current_user.role == 'manager')) :
        if count:
            return crud.voice.get_multi_by_manager_count(db=db, manager_id=manager_id, note_created=note_created)
        voices = crud.voice.get_multi_by_manager(db, manager_id=manager_id, note_created=note_created, skip=skip, limit=limit)
    else :
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return voices

@router.get("/assistant/{assistant_id}", response_model=Union[List[schemas.VoiceReduced], int])
def read_assistant_voices(
    *,
    db: Session = Depends(deps.get_db),
    assistant_id: int,
    skip: int=0,
    limit: int=5,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve untreated voices related to the managers of the assistant.
    Only that assistant and super user can use it
    """
    note_created = False
    if (crud.user.is_superuser(current_user) or (current_user.id  == assistant_id and current_user.role=='assistant')):
        if count:
            return crud.voice.get_multi_by_assistant_count(db, assistant_id=assistant_id, note_created=note_created)
        voices = crud.voice.get_multi_by_assistant(db, assistant_id=assistant_id, note_created=note_created, skip=skip, limit=limit)
    else :
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return voices


@router.get("/patient/{patient_id}", response_model=Union[List[schemas.Voice], int])
def read_patient_voices(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int,
    skip: int=0,
    limit: int=5,
    note_created: Optional[bool]=None,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve patient voices.
    if it's the patient session, it will retrieve all patient voices
    if it's the doctor session , it will retrieve the patient-doctors related voices
    """
    #to change after having the relationship crud
    doctor_idx = db.query(DoctorPatient).filter(DoctorPatient.patient_id == patient_id).\
                                        with_entities(DoctorPatient.doctor_id).all()
    doctor_idx = list(chain(*doctor_idx))

    if (current_user.id  == patient_id):
        if count:
            return crud.voice.get_multi_by_patient_count(db, patient_id=patient_id, note_created=note_created)
        voices = crud.voice.get_multi_by_patient(db, patient_id=patient_id, note_created=note_created, skip=skip, limit=limit)
    elif current_user.role == 'doctor' and current_user.id in doctor_idx:
        if count:
            return crud.voice.get_multi_by_patient_count(db, patient_id=patient_id, doctor_id=current_user.id, note_created=note_created)
        voices = crud.voice.get_multi_by_patient(db, patient_id=patient_id, doctor_id=current_user.id, note_created=note_created, skip=skip, limit=limit)
    else :
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return voices

@router.post("/", response_model=schemas.Voice)
async def create_voice(
    *,
    db: Session = Depends(deps.get_db),
    voice_input : schemas.VoiceCreateUpload,
    current_user: models.User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks
) -> Any:
    """
    Create new item.
    Only doctors and super users can create voices
    """
    if voice_input.voice_file_b64 == '':
        raise HTTPException(
            status_code=405,
            detail="The sent voice is empty.",
        )
    voice_in = schemas.VoiceCreate(path='', doctor_id=voice_input.doctor_id, patient_id=voice_input.patient_id, title=voice_input.title, remarque=voice_input.remarque)
    if (current_user.role != 'doctor' or current_user.id != voice_in.doctor_id) and (not current_user.is_superuser):
        raise HTTPException(
            status_code=401,
            detail="You have not the right the right to write a voice.",
        )
    #to change after having the relationship crud
    patient = crud.user.get_by_id(db=db, id=voice_in.patient_id)
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="No patient with the given id is found in the DB",
        )
    if patient.role != 'patient':
        raise HTTPException(
            status_code=405,
            detail="The id of the given patient is not related to a patient",
        )
    
    doctor_idx = db.query(DoctorPatient).filter(DoctorPatient.patient_id == voice_in.patient_id).\
                                        with_entities(DoctorPatient.doctor_id).all()
    doctor_idx = list(chain(*doctor_idx))

    if not voice_in.doctor_id in doctor_idx:
        raise HTTPException(
                status_code=405,
                detail="This patient is not related to doctor, please ask the admin to relate it to the doctor",
            )
    
    filename = str(uuid.uuid4())
    storage_path = list(Path(os.path.abspath(__file__)).parents)[-2]
    voice_save_path = os.path.abspath(os.path.join(storage_path, 'storage',filename+'_'+voice_input.filename))
    voice_in.path = voice_save_path

    ## base64 to mp3
    encoding_str = voice_input.voice_file_b64
    voice_file = base64.b64decode(encoding_str)
    ##
    async with aiofiles.open(voice_save_path, 'wb') as out_file:
        await out_file.write(voice_file)
    
    voice = crud.voice.create_with_doctor(db=db, obj_in=voice_in, date_creation=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    msg_title = f'Docteur {current_user.full_name} vient de creer une voice avec #id: {voice.id}'
    msg_body = {'voice_id': voice.id, 'title': voice.title, \
            'doctor_id': voice.doctor_id, 'patient_id': voice.patient_id}

    assistants_device = crud.user.get_doctor_assistants(db, doctor_id=voice.doctor_id)
    assistants_device = list(chain(*assistants_device))
    assistants_device = [crud.user.get_user_device(db=db, id=assist_id) for assist_id in assistants_device]
    assistants_device = [token for token in assistants_device if token]

    background_tasks.add_task(send_notification_firebase, msg_title=msg_title, \
                                msg_body=msg_body, to_users=assistants_device)
    #send_notification_firebase(msg=msg, to_users=assistants_device)
    
    return voice

@router.put("/{voice_id}", response_model=schemas.Voice)
def update_voice(
    *,
    db: Session = Depends(deps.get_db),
    voice_in: schemas.VoiceUpdate,
    voice_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Modify voice
    """
    
    voice = crud.voice.get_by_voice_id(db, id=voice_id)
    if not voice:
        raise HTTPException(
            status_code=404,
            detail="No voice fond with given voice_id",
        )
    if (current_user.id == voice.doctor_id and voice.role == "doctor") or current_user.is_superuser:
        voice = crud.voice.update_voice(db=db, db_obj = voice, obj_in=voice_in)
    else:
        raise HTTPException(
            status_code=401,
            detail="No enough permission",
        )
    
    return voice


@router.delete("/{id}", response_model=schemas.Voice)
def delete_voice(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a voice.
    Only superuser or doctor owner of that voice can delete it
    """
    voice = crud.voice.get_by_voice_id(db=db, id=id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    if not crud.user.is_superuser(current_user) and (voice.doctor_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    notes = crud.note.get_many_by_voice_id(db=db, id=voice.id)

    if notes:
        for note in notes:
            crud.note.remove(db=db, id=note.id)
    
    try:
        os.remove(voice.path)
    except OSError:
        pass

    voice = crud.voice.remove(db=db, id=id)
    return voice