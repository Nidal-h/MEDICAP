from typing import Any, List, Optional, Union
from itertools import chain

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from datetime import datetime
from app import crud, models, schemas
from app.api import deps

from app.models.doctor_manager import DoctorManager
from app.models.assistant_manager import AssistantManager
from app.models.doctor_patient import DoctorPatient
from app.models.voice import Voice

router = APIRouter()

@router.get("/", response_model=List[schemas.Note])
def read_notes(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve notes.
    Only super users can retrieve all notes
    """
    if crud.user.is_superuser(current_user):
        notes = crud.note.get_all(db)
    else:
        raise HTTPException(status_code=401, detail="Not enough permissions")
    return notes

 #to change after having the relationship crud
@router.get("/{note_id}", response_model=schemas.NotePlus)
def read_note_by_id(
    *,
    db: Session = Depends(deps.get_db),
    note_id : int,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve note by id.
    Only super user, th assistant of this note, is manaer or the doctor can retrieve it
    """
     #to change after having the relationship crud
    note = crud.note.get_by_note_plus_id(db, id=note_id)
    if note:
        manager_idx = db.query(AssistantManager).filter(AssistantManager.assistant_id == note.assistant_id).\
                                    with_entities(AssistantManager.manager_id).all()
        manager_idx = list(chain(*manager_idx))
        doctor_idx = db.query(Voice).filter(Voice.id == note.voice_id).\
                                    with_entities(Voice.doctor_id).all()
        doctor_idx = list(chain(*doctor_idx))

        if current_user.id == note.assistant_id or current_user.id == note.modifier_id or current_user.is_superuser:
            return note
        elif current_user.id in manager_idx:
            return note
        elif current_user.id in doctor_idx:
            return note
        else:
            raise HTTPException(status_code=400, detail="Not enough permissions")
    else:
        raise HTTPException(status_code=404, detail="No note found with given note id")
    return note

@router.get("/assistant/{assistant_id}", response_model=Union[List[schemas.Note], int])
def get_notes_assistant(
    *,
    db: Session = Depends(deps.get_db),
    assistant_id : int,
    skip: int = 0,
    limit: int = 5,
    validated: Optional[bool]=None,
    treated: Optional[bool]=None,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve notes of an assistant
    Only super user, th assistant , or his manager can retrieve it
    """
     #to change after having the relationship crud
    assistant = crud.user.get_by_id(db, id=assistant_id)
    manager_idx = crud.user.get_assistant_managers(db=db, assistant_id=assistant_id)
    manager_idx = list(chain(*manager_idx))

    if current_user.id != assistant.id and not current_user.id in manager_idx and not current_user.is_superuser:
        raise HTTPException(status_code=401, detail="No enough permissions")

    if assistant and assistant.role == 'assistant':
        if count:
            return crud.note.get_multi_by_assistant_count(db=db, assistant_id=assistant_id, validated=validated, treated=treated)
        notes = crud.note.get_multi_by_assistant(db=db, assistant_id=assistant_id, validated=validated, treated=treated, skip=skip, limit=limit)
        return notes
    else:
        raise HTTPException(status_code=404, detail="No assistant found with given id")


@router.post("/", response_model=schemas.Note)
def create_note(
    *,
    db: Session = Depends(deps.get_db),
    note_in: schemas.NoteCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new note.
    Only assistants and super user can create notes
    """
    if (current_user.role != 'assistant' or current_user.id != note_in.assistant_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=401,
            detail="Not enough permissions",
        )
    
    voice = crud.voice.get_by_voice_id(db, id=note_in.voice_id)
    if not voice:
        raise HTTPException(
            status_code=404,
            detail="The given voice id is not found",
        )
    
    if voice.note_created:
        raise HTTPException(
            status_code=505,
            detail="Note already created for this voice",
        )
    
    assistant_idx = crud.user.get_doctor_assistants(db=db, doctor_id=voice.doctor_id)
    assistant_idx = [assistant.assistant_id for assistant in assistant_idx]

    if not current_user.id in assistant_idx:
        raise HTTPException(
            status_code=401,
            detail="Not related to the doctor oner of the voice",
        )
    
    note = crud.note.create_with_assistant(db=db, obj_in=note_in, date_creation=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    voice = crud.voice.update_voice(db=db, db_obj=voice, obj_in=dict({'note_created':True}))
    return note

@router.put("/{note_id}", response_model=schemas.Note)
def update_note(
    *,
    db: Session = Depends(deps.get_db),
    note_in: schemas.NoteUpdate,
    note_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Modify note
    Assistant doctor or manager related to this note
    """
    
    note = crud.note.get_by_note_id(db, id=note_id)
    
    if note:
        manager_idx = crud.user.get_assistant_managers(db=db, assistant_id=note.assistant_id)
        manager_idx = list(chain(*manager_idx))
        doctor_idx = db.query(Voice).filter(Voice.id == note.voice_id).\
                                    with_entities(Voice.doctor_id).all()
        doctor_idx = list(chain(*doctor_idx))
        
        if current_user.id in doctor_idx or current_user.is_superuser:
            note_in.modifier_id = current_user.id
            note_in.date_modification = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            note = crud.note.update_note(db=db, db_obj = note, obj_in=note_in)
        elif (current_user.id == note.assistant_id and not note.validated) or current_user.id == note.modifier_id \
             or (current_user.id in manager_idx and not note.validated):
            note_in.modifier_id = current_user.id
            note_in.validated = note.validated
            note_in.date_modification = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            note = crud.note.update_note(db=db, db_obj = note, obj_in=note_in)
            return note
        else:
            raise HTTPException(status_code=400, detail="Not enough permissions")
    else:
        raise HTTPException(
            status_code=404,
            detail="No note fund with the given id.",
        )
    
    return note

#############################################

@router.get("/doctor/{doctor_id}", response_model=Union[List[schemas.Note], int])
def read_doctor_notes(
    *,
    db: Session = Depends(deps.get_db),
    doctor_id: int,
    skip: int = 0,
    limit: int = 5,
    validated: Optional[bool]=None,
    treated: Optional[bool]=None,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve doctor notes.
    Only a doctor or super user can retrieve them
    """
    if current_user.role != "doctor" and not current_user.is_superuser:
        HTTPException(status_code=400, detail="Not enough permissions")

    if crud.user.is_superuser(current_user) or current_user.id  == doctor_id:
        if count:
            return crud.note.get_multi_by_doctor_id_count(db=db, validated=validated, doctor_id=doctor_id, treated=treated)
        notes = crud.note.get_multi_by_doctor_id(db, doctor_id=doctor_id, validated=validated, treated=treated, skip=skip, limit=limit)
    else :
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return notes

@router.get("/search/", response_model=List[schemas.Search])
def search_note(
        *, 
        db: Session = Depends(deps.get_db),
        content_text: Optional[str]='',
        date_creation_before: Optional[datetime]='', 
        date_creation_after: Optional[datetime]='',
        patient_name: Optional[str]='',
        validated: Optional[bool]=None,
        treated: Optional[bool]=None,
        current_user: models.User = Depends(deps.get_current_active_user)) -> Any:
    """
    Search for notes
    """
    user_id = current_user.id
    if (current_user.role != 'manager' or not current_user.is_superuser):
        notes = crud.note.search_note(db=db, user_idx=[user_id], content_text=content_text, 
            date_creation_before=date_creation_before, date_creation_after=date_creation_after,
            patient_name=patient_name, treated=treated, validated=validated)
        print(notes)
        return notes
    elif current_user.is_superuser:
        notes = crud.note.search_note(db=db, user_idx=[], content_text=content_text, 
            date_creation_before=date_creation_before, date_creation_after=date_creation_after,
            patient_name=patient_name, treated=treated, validated=validated)
        return notes

    elif current_user.role == 'manager':
        assistants_idx = crud.user.get_manager_assistants(db=db, 
            manager_id=current_user.id)
        assistants_idx = list(chain(*assistants_idx))
        doctor_idx = crud.user.get_manager_doctors(db=db, 
            manager_id=current_user.id)
        doctor_idx = list(chain(*doctor_idx))
        
        indices = doctor_idx + assistants_idx + [current_user.id]

        notes = crud.note.search_note(db=db, user_idx=indices, content_text=content_text, 
            date_creation_before=date_creation_before, date_creation_after=date_creation_after,
            patient_name=patient_name, treated=treated, validated=validated)
        return notes
    else :
        raise HTTPException(status_code=400, detail="Not enough permissions")


@router.get("/manager/{manager_id}", response_model=Union[List[schemas.Note], int])
def read_manager_notes(
    *,
    db: Session = Depends(deps.get_db),
    manager_id: int,
    skip: int = 0,
    limit: int = 5,
    validated: Optional[bool]=None,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve voices.
    manager or super user
    """
    if current_user.role != "manager" and not current_user.is_superuser:
        HTTPException(status_code=400, detail="Not enough permissions")
    if crud.user.is_superuser(current_user) or current_user.id  == manager_id:
        if count:
            return crud.note.get_multi_by_manager_count(db=db, manager_id=manager_id, validated=validated)
        notes = crud.note.get_multi_by_manager(db, manager_id=manager_id, validated=validated, skip=skip, limit=limit)
        return notes
    else :
        raise HTTPException(status_code=400, detail="Not enough permissions")
    

@router.get("/patient/{patient_id}", response_model=Union[List[schemas.Note], int])
def read_patient_voices(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int,
    skip: int = 0,
    limit: int = 5,
    validated: Optional[bool]=None,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve notes.
    Only the patient or his doctor can retrieve the patient voices (also super user)
    """
    doctor_idx = db.query(DoctorPatient).filter(DoctorPatient.patient_id == patient_id).with_entities(DoctorPatient.doctor_id).all()
    doctor_idx = list(chain(*doctor_idx))

    if crud.user.is_superuser(current_user) or current_user.id  == patient_id or current_user.id in doctor_idx:
        if count:
            return crud.note.get_multi_by_patient_count(db=db, patient_id=patient_id, validated=validated)
        notes = crud.note.get_multi_by_patient(db, patient_id=patient_id, validated=validated, skip=skip, limit=limit)
        return notes
    else :
        raise HTTPException(status_code=400, detail="Not enough permissions")
    


@router.get("/remarque_note/{note_id}", response_model=List[schemas.RemarqueNote])
def read_remarques_note_by_id(
    *,
    db: Session = Depends(deps.get_db),
    note_id : int,
    skip: int = 0,
    limit: int = 20,
    current_user: models.User = Depends(deps.get_current_active_user),
    
) -> Any:
    """
    Retrieve notes remarques by id.
    Only super user, the assistant of this note, is manager can retrieve it
    """
     #to change after having the relationship crud
    note = crud.note.get_by_note_id(db, id=note_id)
    if note:
        manager_idx = db.query(AssistantManager).filter(AssistantManager.assistant_id == note.assistant_id).\
                                    with_entities(AssistantManager.manager_id).all()
        manager_idx = list(chain(*manager_idx))

        doctor_idx = crud.note.get_note_doctor(db, id=note_id)
        print('doctor_idx', doctor_idx)
        doctor_idx = list(chain(*doctor_idx))

        remarques_note = crud.note.get_remarques_by_note_id(db=db,id=note_id, skip=skip, limit=limit)
        if current_user.id == note.assistant_id or current_user.id == note.modifier_id \
            or current_user.is_superuser:
            return remarques_note
        elif current_user.id in manager_idx:
            return remarques_note
        elif current_user.id in doctor_idx:
            return remarques_note
        else:
            raise HTTPException(status_code=400, detail="Not enough permissions")
    else:
        raise HTTPException(status_code=404, detail="No remarque note found with given note id")

@router.post("/remarque_note", response_model=schemas.RemarqueNote)
def create_remarque_note(
    *,
    db: Session = Depends(deps.get_db),
    remarque_note_in: schemas.RemarqueNoteCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new remarque note.
    Only assistants, managers and super user can create notes
    """
    note = crud.note.get_by_note_id(db, id=remarque_note_in.note_id)
    if not note:
        raise HTTPException(
            status_code=404,
            detail="The given note id is not found",
        )
    
    manager_idx = crud.user.get_assistant_managers(db, assistant_id=note.assistant_id)
    manager_idx = list(chain(*manager_idx))

    doctor_idx = crud.note.get_note_doctor(db, id=remarque_note_in.note_id)
    doctor_idx = list(chain(*doctor_idx))

    if (current_user.role != 'assistant' or current_user.id != note.assistant_id) and \
            not current_user.is_superuser and not current_user.id in manager_idx \
            and not current_user.id in doctor_idx :
        raise HTTPException(
            status_code=401,
            detail="Not enough permissions",
        )
    
    if current_user.id != remarque_note_in.creator_id:
        raise HTTPException(
            status_code=401,
            detail="Not enough permissions",
        )

    remarque_note = crud.note.create_remarque_note(db=db, obj_in=remarque_note_in, date_creation=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return remarque_note