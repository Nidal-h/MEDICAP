from typing import Any, List, Union, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app.models.doctor_patient import DoctorPatient
from app.schemas.doctor_patient import DoctorPatientCreate, DoctorPatientUpdate

from uuid import uuid4
from app import crud, models, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_new_account_email, generate_confirmation_token

from itertools import chain

router = APIRouter()


@router.get("/", response_model=Union[List[schemas.User], int])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    Only super user can retrieve a list of all users
    """
    if count:
        count = crud.user.get_multi_count(db)
        return count
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/doctors", response_model=Union[List[schemas.User], int])
def read_doctors(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve doctors.
    Only super user can retrieve a list of all users
    """
    if count:
        count = crud.user.get_multi_doctors_count(db)
        return count
    users = crud.user.get_multi_doctors(db, skip=skip, limit=limit)
    return users

@router.get("/managers", response_model=Union[List[schemas.User], int])
def read_managers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve managers.
    Only super user can retrieve a list of all users
    """
    if count:
        count = crud.user.get_multi_managers_count(db)
        return count
    users = crud.user.get_multi_managers(db, skip=skip, limit=limit)
    return users

@router.get("/assistants", response_model=Union[List[schemas.User], int])
def read_assistants(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve assistants.
    Only super user can retrieve a list of all users
    """
    if count:
        count = crud.user.get_multi_assistants_count(db)
        return count
    users = crud.user.get_multi_assistants(db, skip=skip, limit=limit)
    return users

@router.get("/patients", response_model=Union[List[schemas.User], int])
def read_patients(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    count: Optional[bool]=None,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve patients.
    Only super user can retrieve a list of all users
    """
    if count:
        count = crud.user.get_multi_patients_count(db)
        return count
    users = crud.user.get_multi_patients(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=Union[schemas.User, schemas.UserLoginOrCreationErr])
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_user),
    background_tasks: BackgroundTasks
) -> Any:
    """
    Create new user.
    Only super user can create users and doctors who can create patient
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=401,
            detail="Only super user can create users or doctors who can create patient",
        )
    user = crud.user.get_by_email(db, email=user_in.email)
    
    user_in.is_active = False
    
    if user:
        #raise HTTPException(status_code=400, detail="The user with this username already exists in the system.")
        return schemas.UserLoginOrCreationErr(msg='Un utilisateur avec la meme adresse est déjà enregistré')

    user = crud.user.create(db, obj_in=user_in)
    if settings.EMAILS_ENABLED and user_in.email and user_in.role != 'patient':
        confirmation_token = generate_confirmation_token(email=user_in.email)
        background_tasks.add_task(send_new_account_email, email_to=user_in.email, \
                               username=user_in.email, password=user_in.password, token=confirmation_token)
        # send_new_account_email(
        #     email_to=user_in.email, username=user_in.email, password=user_in.password, token=confirmation_token
        # )
    return user

@router.post("/create/patient", response_model=Union[schemas.User, schemas.UserLoginOrCreationErr])
def create_patient_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new patient user.
    Only doctor who can create patient
    """

    if (current_user.role != 'doctor' or user_in.role != 'patient'):
        raise HTTPException(
            status_code=401,
            detail="Only super user can create users or doctors who can create patient",
        )
    
    if user_in.email == 'empty@medicaligne.fr' or user_in.email == '':
        user_in.email = str(user_in.uuid)+"@medicaligne.fr" if user_in.uuid \
                            else str(uuid4())+"@medicaligne.fr"
    if user_in.password == 'empty' or user_in.password == '':
        user_in.password = str(user_in.uuid) if user_in.uuid \
                            else str(uuid4())

    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        return schemas.UserLoginOrCreationErr(msg='Un utilisateur avec la meme adresse est déjà enregistré')
        #raise HTTPException(status_code=400,detail="The user with this username already exists in the system.")
    
    user = crud.user.get_by_name_birthday(db, full_name=user_in.full_name, birth_date= user_in.birth_date)
    if user:
        return schemas.UserLoginOrCreationErr(msg='Un utilisateur avec la meme nom et date de naissance deja existant')
        #raise HTTPException(status_code=400,detail="The user with this username already exists in the system.")
    
    user_in.is_active = False
    user_in.is_superuser = False
    

    user = crud.user.create(db, obj_in=user_in)
    doctor_patient = schemas.DoctorPatientCreate(doctor_id=current_user.id, patient_id=user.id)
    crud.user.create_doctor_patient(db=db, obj_in=doctor_patient)
    
    if settings.EMAILS_ENABLED and user_in.email and user_in.role != 'patient':
        send_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password, token=""
        )
    return user

@router.put("/update/patient/{user_id}", response_model=schemas.User)
def update_patient(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a patient.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )

    if not user.role == "patient":
        raise HTTPException(status_code=401,
            detail="The user is not a patient")

    doctor_idx = db.query(DoctorPatient).filter(DoctorPatient.patient_id == user_id).\
                                        with_entities(DoctorPatient.doctor_id).all()
    doctor_idx = list(chain(*doctor_idx))
 
    if ((current_user.role != 'doctor') or not current_user.id in doctor_idx) \
        and not (current_user.is_superuser):
        raise HTTPException(status_code=401,
            detail="You have not enough rights to modify the patient")

    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user

@router.delete("/patient/{user_id}", response_model=Union[schemas.DoctorPatientInDB, str])
def delete_patient(
    *,
    db: Session = Depends(deps.get_db),
    patient_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a patient.
    """
    doctor_id = current_user.id
    doctor = crud.user.get(db, id=current_user.id)
    patient = crud.user.get(db, id=patient_id)
    
    if current_user.role != 'doctor' and not current_user.is_superuser:
        raise HTTPException(
            status_code=401, detail="Only doctors and super users can remove this relationship"
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

@router.delete("/{id}", response_model=schemas.User)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a user.
    """
    user = crud.user.get_by_id(db=db, id=id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not crud.user.is_superuser(current_user):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    user = crud.user.remove(db=db, id=id)
    return user

@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    password: str = Body(None),
    full_name: str = Body(None),
    email: EmailStr = Body(None),
    profile_bs64: str = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.UserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if full_name is not None:
        user_in.full_name = full_name
    if email is not None:
        user_in.email = email
    if profile_bs64 is not None:
        user_in.profile_bs64 = profile_bs64
    if not current_user.is_superuser:
        user_in.is_superuser = current_user.is_superuser
        user_in.is_active = current_user.is_active
    
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/me", response_model=schemas.User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.post("/open", response_model=schemas.User)
def create_user_open(
    *,
    db: Session = Depends(deps.get_db),
    password: str = Body(...),
    email: EmailStr = Body(...),
    full_name: str = Body(None),
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = crud.user.get_by_email(db, email=email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    user_in = schemas.UserCreate(password=password, email=email, full_name=full_name)
    user = crud.user.create(db, obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    return user
    

    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user

@router.get("/patient/{patient_id}", response_model=schemas.User)
def read_patient_by_id(
    patient_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific patient by id.
    Need to be related to that patient
    """
    user = crud.user.get(db, id=patient_id)

    if user.role !='patient':
        raise HTTPException(
            status_code=400, detail="The given patient id don't belong to a patient"
        )
    
    assistants_idx = crud.user.get_patient_assistants(db=db, patient_id=patient_id)
    manager_idx = crud.user.get_patient_managers(db=db, patient_id=patient_id)
    doctor_idx = crud.user.get_patient_doctors(db=db, patient_id=patient_id)
    doctor_voices_idx = crud.user.get_patient_doctors_voices(db=db, patient_id=patient_id)
    authorized_idx = assistants_idx + manager_idx
    
    if user.id == current_user.id or current_user.id in doctor_idx or current_user.id in doctor_voices_idx:
        return user
    elif current_user.id in authorized_idx or current_user.is_superuser:
        user = user.__dict__
        #user['full_name'] = 'Hidden Name'
        return user
    else:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )