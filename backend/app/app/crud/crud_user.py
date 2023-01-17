from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

from app.models.doctor_manager import DoctorManager
from app.schemas.doctor_manager import DoctorManagerCreate, DoctorManagerUpdate

from app.models.doctor_patient import DoctorPatient
from app.schemas.doctor_patient import DoctorPatientCreate, DoctorPatientUpdate

from app.models.assistant_manager import AssistantManager
from app.schemas.assistant_manager import AssistantManagerCreate, AssistantManagerUpdate

from app.models.note import Note
from app.models.voice import Voice

from datetime import datetime
from uuid import uuid4


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_id(self, db: Session, *, id: int) -> User:
        user = db.query(User).filter(User.id == id).first()
        return user

    def get_by_name_birthday(self, db: Session, *, full_name: str, birth_date: datetime) -> User:
        user = db.query(User).filter(User.full_name == full_name, 
                User.birth_date == birth_date).first()
        return user

    def get_multi_count(
        self, db: Session
    ) -> int:
        return db.query(User).count()
    
    def get_multi_doctors(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        return db.query(User).filter(User.role == 'doctor').offset(skip).limit(limit).all()
    
    def get_multi_doctors_count(
        self, db: Session
    ) -> int:
        return db.query(User).filter(User.role == 'doctor').count()

    def get_multi_managers(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        return db.query(User).filter(User.role == 'manager').offset(skip).limit(limit).all()
    
    def get_multi_managers_count(
        self, db: Session
    ) -> int:
        return db.query(User).filter(User.role == 'manager').count()

    def get_multi_assistants(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        return db.query(User).filter(User.role == 'assistant').offset(skip).limit(limit).all()
    
    def get_multi_assistants_count(
        self, db: Session
    ) -> int:
        return db.query(User).filter(User.role == 'assistant').count()

    def get_multi_patients(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        return db.query(User).filter(User.role == 'patient').offset(skip).limit(limit).all()
    
    def get_multi_patients_count(
        self, db: Session
    ) -> int:
        return db.query(User).filter(User.role == 'patient').count()

    def get(self, db: Session, id: int) -> Optional[User]:
        return self.get_by_id(db=db, id=id)

    def update_user_device(self, db: Session, *, id: int, token: str) -> User:
        user = db.query(User).filter(User.id == id).first()
        user = self.update(db=db, db_obj=user, obj_in=dict({'firebase_device_token':token}))
        return user

    def get_user_device(self, db: Session, *, id: int) -> str:
        user = db.query(User).filter(User.id == id).first()
        return user.firebase_device_token

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
            role = obj_in.role,
            birth_date=obj_in.birth_date,
            uuid=uuid4(),
            profile_bs64=obj_in.profile_bs64,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser
    
    def role(self, user: User) -> str:
        return user.role

    def create_doctor_manager(self, db: Session, *, obj_in: DoctorManagerCreate) -> DoctorManager:
        db_obj = DoctorManager(
            doctor_id=obj_in.doctor_id,
            manager_id=obj_in.manager_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_doctor_manager_by_idx(self, db: Session, *, obj_in: DoctorManagerCreate) -> Optional[DoctorManager]:
        return db.query(DoctorManager).filter(DoctorManager.doctor_id==obj_in.doctor_id,
            DoctorManager.manager_id==obj_in.manager_id).first()
    
    def remove_doctor_manager(self, db: Session, *, obj_in: DoctorManagerUpdate) -> DoctorManager:
        obj = db.query(DoctorManager).filter(DoctorManager.doctor_id==obj_in.doctor_id,
            DoctorManager.manager_id==obj_in.manager_id).first()
        db.delete(obj)
        db.commit()
        return obj
    
    def create_doctor_patient(self, db: Session, *, obj_in: DoctorPatientCreate) -> DoctorPatient:
        db_obj = DoctorPatient(
            doctor_id=obj_in.doctor_id,
            patient_id=obj_in.patient_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_doctor_patient_by_idx(self, db: Session, *, obj_in: DoctorPatientCreate) -> Optional[DoctorPatient]:
        obj = db.query(DoctorPatient).filter(DoctorPatient.doctor_id==obj_in.doctor_id, DoctorPatient.patient_id==obj_in.patient_id).first()
        return obj
    
    def get_doctor_patients(self, db: Session, *, doctor_id: int) -> List[DoctorPatient]:
        objs = db.query(DoctorPatient.patient_id).filter(DoctorPatient.doctor_id==doctor_id).distinct()
        return objs
    
    def remove_doctor_patient(self, db: Session, *, obj_in: DoctorPatientUpdate) -> DoctorPatient:
        obj = db.query(DoctorPatient).filter(DoctorPatient.doctor_id==obj_in.doctor_id,
            DoctorPatient.patient_id==obj_in.patient_id).first()
        db.delete(obj)
        db.commit()
        return obj
    
    def create_assistant_manager(self, db: Session, *, obj_in: AssistantManagerCreate) -> AssistantManager:
        db_obj = AssistantManager(
            assistant_id=obj_in.assistant_id,
            manager_id=obj_in.manager_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_assistant_manager_by_idx(self, db: Session, *, obj_in: AssistantManagerCreate) -> Optional[AssistantManager]:
        return db.query(AssistantManager).filter(AssistantManager.assistant_id==obj_in.assistant_id,
            AssistantManager.manager_id==obj_in.manager_id).first()
    
    def get_manager_assistants(self, db: Session, *, manager_id: int) -> List[AssistantManager]:
        objs = db.query(AssistantManager.assistant_id).filter(AssistantManager.manager_id==manager_id).distinct()
        return objs

    def get_manager_doctors(self, db: Session, *, manager_id: int) -> List[DoctorManager]:
        objs = db.query(DoctorManager.doctor_id).filter(DoctorManager.manager_id==manager_id).distinct()
        return objs

    def remove_assistant_manager(self, db: Session, *, obj_in: AssistantManagerUpdate) -> AssistantManager:
        obj = db.query(AssistantManager).filter(AssistantManager.assistant_id==obj_in.assistant_id,
            AssistantManager.manager_id==obj_in.manager_id).first()
        db.delete(obj)
        db.commit()
        return obj
    
    def get_assistant_managers(self, db: Session, *, assistant_id: int) -> List[AssistantManager]:
        objs = db.query(AssistantManager.manager_id).filter(AssistantManager.assistant_id==assistant_id).distinct()
        return objs
    
    def get_patient_assistants(self, db: Session, *, patient_id: int) -> List[int]:
        assistant_idx = db.query(Note).join(Voice, Note.voice_id == Voice.id).filter(Voice.patient_id==patient_id)\
                .with_entities(Note.assistant_id).distinct()
        assistant_idx = [assistant.assistant_id for assistant in assistant_idx]
        return assistant_idx
    
    def get_patient_managers(self, db: Session, *, patient_id: int) -> List[int]:
        manager_idx = db.query(DoctorManager).join(DoctorPatient, DoctorManager.doctor_id == DoctorPatient.doctor_id)\
                    .filter(DoctorPatient.patient_id==patient_id).with_entities(DoctorManager.manager_id).distinct()
        manager_idx = [manager.manager_id for manager in manager_idx]
        return manager_idx
    
    def get_patient_doctors(self, db: Session, *, patient_id: int) -> List[int]:
        doctor_idx = db.query(DoctorPatient).filter(DoctorPatient.patient_id==patient_id)\
                        .with_entities(DoctorPatient.doctor_id).distinct()
        doctor_idx = [doctor.doctor_id for doctor in doctor_idx]
        return doctor_idx

    def get_patient_doctors_voices(self, db: Session, *, patient_id: int) -> List[int]:
        doctor_idx = db.query(Voice).filter(Voice.patient_id==patient_id)\
                        .with_entities(Voice.doctor_id).distinct()
        doctor_idx = [doctor.doctor_id for doctor in doctor_idx]
        return doctor_idx
    
    def get_doctor_managers(self, db: Session, *, doctor_id: int) -> List[DoctorManager]:
        objs = db.query(DoctorManager.manager_id).filter(DoctorManager.doctor_id==doctor_id).distinct()
        return objs
    
    def get_doctor_assistants(self, db: Session, *, doctor_id: int) -> List[AssistantManager]:
        objs = db.query(DoctorManager).join(AssistantManager, DoctorManager.manager_id == AssistantManager.manager_id)\
            .filter(DoctorManager.doctor_id==doctor_id).with_entities(AssistantManager.assistant_id).distinct()
        return objs
    
user = CRUDUser(User)
