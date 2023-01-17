from typing import Any, List, Union

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_new_account_email

router = APIRouter()



@router.get("/doctor_manager/{doctor_id}/{manager_id}", response_model=schemas.DoctorManagerInDB)
def create_doctor_manager(
    doctor_id: int,
    manager_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Create doctor manager relationship
    Only super users can create this relationship
    """
    doctor = crud.user.get(db, id=doctor_id)
    manager = crud.user.get(db, id=manager_id)
    
    if not doctor or doctor.role != 'doctor':
        raise HTTPException(
            status_code=404, detail="No Doctor found with given doctor_id"
        )
    if not manager or manager.role != 'manager':
        raise HTTPException(
            status_code=404, detail="No Manager found with given manager_id"
        )
    obj_in = schemas.DoctorManagerCreate(doctor_id=doctor_id, manager_id=manager_id)
    
    relationship = crud.user.get_doctor_manager_by_idx(db, obj_in=obj_in)
    if relationship:
        return relationship

    doctor_manager = crud.user.create_doctor_manager(db=db, obj_in=obj_in)
    return doctor_manager

@router.get("/doctor_patient/{doctor_id}/{patient_id}", response_model=schemas.DoctorPatientInDB)
def create_doctor_patient(
    doctor_id: int,
    patient_id: int,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Create doctor patient relationship.
    Doctors and super users can create this relationship
    """

    doctor = crud.user.get(db, id=doctor_id)
    patient = crud.user.get(db, id=patient_id)
    
    if current_user.role != 'doctor' and not current_user.is_superuser:
        raise HTTPException(
            status_code=401, detail="Only doctoors and super users can create this relationship"
        )
    
    if current_user.role == 'doctor' and current_user.id != doctor_id:
        raise HTTPException(
            status_code=401, detail="You can not create relationships for other doctors"
        )
    
    if not doctor or doctor.role != 'doctor':
        raise HTTPException(
            status_code=404, detail="No Doctor found with given doctor_id"
        )
    if not patient or patient.role != 'patient':
        raise HTTPException(
            status_code=404, detail="No Patient found with given patient_id"
        )
    obj_in = schemas.DoctorPatientCreate(doctor_id=doctor_id, patient_id=patient_id)

    relationship = crud.user.get_doctor_patient_by_idx(db, obj_in=obj_in)
    if relationship:
        return relationship
    
    doctor_patient = crud.user.create_doctor_patient(db=db, obj_in=obj_in)
    return doctor_patient


@router.get("/assistant_manager/{assistant_id}/{manager_id}", response_model=schemas.AssistantManagerInDB)
def create_assistant_manager(
    assistant_id: int,
    manager_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Create doctor manager relationship
    Only super users can create this relationship
    """

    assistant = crud.user.get(db, id=assistant_id)
    manager = crud.user.get(db, id=manager_id)
    
    if not assistant or assistant.role != 'assistant':
        raise HTTPException(
            status_code=404, detail="No assistant found with given assistant_id"
        )
    if not manager or manager.role != 'manager':
        raise HTTPException(
            status_code=404, detail="No Manager found with given manager_id"
        )
    obj_in = schemas.AssistantManagerCreate(assistant_id=assistant_id, manager_id=manager_id)
    relationship = crud.user.get_assistant_manager_by_idx(db, obj_in=obj_in)
    if relationship:
        return relationship
    assistant_manager = crud.user.create_assistant_manager(db=db, obj_in=obj_in)
    return assistant_manager


########################

@router.get("/get/patients/doctor/{doctor_id}/", response_model=List[schemas.User])
def get_patients_doctor(
    doctor_id: int,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get doctor's patients relationship.
    Doctors and super users can get this relationships
    """

    doctor = crud.user.get(db, id=doctor_id)
    
    if current_user.role != 'doctor' and not current_user.is_superuser:
        raise HTTPException(
            status_code=401, detail="Only doctoors and super users can create this relationship"
        )
    
    if current_user.role == 'doctor' and current_user.id != doctor_id:
        raise HTTPException(
            status_code=401, detail="You can not create relationships for other doctors"
        )
    
    if not doctor or doctor.role != 'doctor':
        raise HTTPException(
            status_code=404, detail="No Doctor found with given doctor_id"
        )
    
    patients_idx = crud.user.get_doctor_patients(db=db, doctor_id=doctor_id)
    patients = [crud.user.get_by_id(db=db,id=patient.patient_id) for patient in patients_idx]
    return patients

@router.get("/get/assistants/manager/{manager_id}/", response_model=List[schemas.User])
def get_assistants_manager(
    manager_id: int,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get manager's assistant relationship.
    managers and super users can get this relationships
    """

    manager = crud.user.get(db, id=manager_id)
    
    if current_user.role != 'manager' and not current_user.is_superuser:
        raise HTTPException(
            status_code=401, detail="Only managers and super users can create this relationship"
        )
    
    if current_user.role == 'manager' and current_user.id != manager_id:
        raise HTTPException(
            status_code=401, detail="You can not cehck relationships for other managers"
        )
    
    if not manager or manager.role != 'manager':
        raise HTTPException(
            status_code=404, detail="No Manager found with given manager_id"
        )
    
    assistants_idx = crud.user.get_manager_assistants(db=db, manager_id=manager_id)
    assistants = [crud.user.get_by_id(db=db,id=assistant.assistant_id) for assistant in assistants_idx]
    return assistants

@router.get("/get/managers/doctor/{doctor_id}/", response_model=List[schemas.User])
def get_managers_doctor(
    doctor_id: int,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get doctor's manager relationship.
    doctors and super users can get this relationships
    """

    doctor = crud.user.get(db, id=doctor_id)
    
    if current_user.role != 'doctor' and not current_user.is_superuser:
        raise HTTPException(
            status_code=401, detail="Only doctors and super users can create this relationship"
        )
    
    if current_user.role == 'doctor' and current_user.id != doctor_id:
        raise HTTPException(
            status_code=401, detail="You can not chck relationships for other doctors"
        )
    
    if not doctor or doctor.role != 'doctor':
        raise HTTPException(
            status_code=404, detail="No doctor found with given doctor_id"
        )
    
    manager_idx = crud.user.get_doctor_managers(db=db, doctor_id=doctor_id)
    managers = [crud.user.get_by_id(db=db,id=manager.manager_id) for manager in manager_idx]
    return managers

#######################

@router.delete("/doctor_manager/{doctor_id}/{manager_id}", response_model=Union[schemas.DoctorManagerInDB, str])
def delete_doctor_manager(
    doctor_id: int,
    manager_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Delete doctor manager relationship
    Only super users can create this relationship
    """
    doctor = crud.user.get(db, id=doctor_id)
    manager = crud.user.get(db, id=manager_id)
    
    if not doctor or doctor.role != 'doctor':
        raise HTTPException(
            status_code=404, detail="No Doctor found with given doctor_id"
        )
    if not manager or manager.role != 'manager':
        raise HTTPException(
            status_code=404, detail="No Manager found with given manager_id"
        )
    obj_in = schemas.DoctorManagerUpdate(doctor_id=doctor_id, manager_id=manager_id)
    
    
    relationship = crud.user.get_doctor_manager_by_idx(db, obj_in=obj_in)
    
    if not relationship:
        return 'relationship does not exist'
    
    relationship = crud.user.remove_doctor_manager(db, obj_in=obj_in)
    return relationship

@router.delete("/doctor_patient/{doctor_id}/{patient_id}", response_model=Union[schemas.DoctorPatientInDB, str])
def delete_doctor_patient(
    doctor_id: int,
    patient_id: int,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Remove doctor patient relationship.
    Doctors and super users can create this relationship
    """

    doctor = crud.user.get(db, id=doctor_id)
    patient = crud.user.get(db, id=patient_id)
    
    if current_user.role != 'doctor' and not current_user.is_superuser:
        raise HTTPException(
            status_code=401, detail="Only doctoors and super users can remove this relationship"
        )
    
    if current_user.role == 'doctor' and current_user.id != doctor_id:
        raise HTTPException(
            status_code=401, detail="You can not remove relationships for other doctors"
        )
    
    if not doctor or doctor.role != 'doctor':
        raise HTTPException(
            status_code=404, detail="No Doctor found with given doctor_id"
        )
    if not patient or patient.role != 'patient':
        raise HTTPException(
            status_code=404, detail="No Patient found with given patient_id"
        )
    
    obj_in = schemas.DoctorPatientUpdate(doctor_id=doctor_id, patient_id=patient_id)

    relationship = crud.user.get_doctor_patient_by_idx(db, obj_in=obj_in)
    
    if not relationship:
        return 'relationship does not exist'
    
    relationship = crud.user.remove_doctor_patient(db, obj_in=obj_in)
    return relationship

@router.delete("/assistant_manager/{assistant_id}/{manager_id}", response_model=schemas.AssistantManagerInDB)
def delete_assistant_manager(
    assistant_id: int,
    manager_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Remove assistant manager relationship
    Only super users can create this relationship
    """

    assistant = crud.user.get(db, id=assistant_id)
    manager = crud.user.get(db, id=manager_id)
    
    if not assistant or assistant.role != 'assistant':
        raise HTTPException(
            status_code=404, detail="No assistant found with given assistant_id"
        )
    if not manager or manager.role != 'manager':
        raise HTTPException(
            status_code=404, detail="No Manager found with given manager_id"
        )
    obj_in = schemas.AssistantManagerUpdate(assistant_id=assistant_id, manager_id=manager_id)
    relationship = crud.user.get_assistant_manager_by_idx(db, obj_in=obj_in)
    if not relationship:
        return 'relationship does not exist'
    
    relationship = crud.user.remove_assistant_manager(db=db, obj_in=obj_in)
    return relationship
