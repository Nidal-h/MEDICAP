from typing import List, Optional, Any, Dict, Optional, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.note import Note
from app.models.remarque_note import RemarqueNote
from app.models.voice import Voice
from app.models.user import User
from app.models.doctor_manager import DoctorManager
from app.models.assistant_manager import AssistantManager
from app.models.doctor_patient import DoctorPatient

from datetime import datetime
from app.schemas.note import NoteCreate, NoteUpdate, NotePlus
from app.schemas.user_doctor import Doctor
from app.schemas.user_patient import Patient

from sqlalchemy import inspect, and_, or_, not_


class CRUDNote(CRUDBase[Note, NoteCreate, NoteUpdate]):
    def create_with_assistant(
        self, db: Session, *, obj_in: NoteCreate, date_creation: datetime
    ) -> Note:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, date_creation = date_creation)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_note(
        self, db: Session, *, db_obj: Note, obj_in: Union[NoteUpdate, Dict[str, Any]]
    ) -> Note:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def get_all(
        self, db: Session
    ) -> List[Note]:
        return (
            db.query(self.model)
            .all()
        )
    
    def get_note_doctor(
        self, db: Session, *, id: int) -> Any:
        return (db.query(Voice.doctor_id)
            .join(Note, Note.voice_id == Voice.id)
            .filter(Note.id == id)
            .distinct())

    def search_note(
        self, db: Session, *, user_idx: List[int], content_text: Optional[str]='', \
        date_creation_before: Optional[datetime]='', date_creation_after: Optional[datetime]='',\
        patient_name: Optional[str]='', validated: Optional[bool]=None, treated: Optional[bool]=None) -> Any:

        if date_creation_before == '':
            date_creation_before = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
        if date_creation_after == '':
            date_creation_after = '1999-01-01'
        
        all_elements = False
        
        if user_idx == []:
            all_elements = True
        

        table = (db.query(Voice.id.label('voice_id'), Voice.doctor_id, Voice.patient_id,\
            Voice.title, Voice.remarque, Voice.date_creation, Voice.note_created,\
            Note.content_txt, Note.id.label('note_id'), Note.validated, Note.assistant_id,\
            Note.modifier_id, Note.date_modification.label('note_date_modification'))
            .outerjoin(Note, Note.voice_id == Voice.id)
            .join(User, Voice.patient_id == User.id))

        # user id condition and patient name
        sub_filter_condition_1 = or_(Voice.doctor_id.in_(user_idx),
                            Note.modifier_id.in_(user_idx),
                            Note.assistant_id.in_(user_idx))
        

        filter_condition_1 = and_(sub_filter_condition_1, 
                        User.full_name.ilike('%'+patient_name+'%'))
        
        # date and content condition
        sub_filter_condition = or_(
                            Note.date_creation.between(date_creation_after, date_creation_before), 
                            Voice.date_creation.between(date_creation_after, date_creation_before)
                            )

        sub_filter_condition_0 = or_(Note.content_txt.ilike('%'+content_text+'%'), 
                    Voice.title.ilike('%'+content_text+'%'))

        filter_condition_2 = and_(sub_filter_condition_0, sub_filter_condition)

        # Treated and validated condition
        if treated == False:
            sub_filter_condition_3 = Note.modifier_id.is_(None)
        elif treated == True:
            sub_filter_condition_3 = Note.modifier_id.is_not(None)
        else:
            sub_filter_condition_3 = True

        if validated == False:
            sub_filter_condition_2 = (Note.validated == False)
        elif validated == True:
            sub_filter_condition_2 = (Note.validated == True)
        else:
            sub_filter_condition_2 = True

        filter_condition_3 = and_(sub_filter_condition_3, sub_filter_condition_2)

        filter_condition = and_(filter_condition_1, filter_condition_2)
        filter_condition = and_(filter_condition_3, filter_condition)

        results = (table
            .filter(filter_condition)
            .all())
        
        return results


    def get_multi_by_doctor_id(self, db: Session, *, doctor_id: int, validated: Optional[bool]=None, treated: Optional[bool]=None, skip: int=0, limit: int = 5) -> List[Note]:
        
        if type(validated) is bool and treated == True:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.validated == validated, Note.modifier_id.is_not(None))
            .offset(skip).limit(limit)
            .all())

        elif type(validated) is bool and treated == False:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.validated == validated, Note.modifier_id.is_(None))
            .offset(skip).limit(limit)
            .all())
        elif type(validated) is bool:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.validated == validated)
            .offset(skip).limit(limit)
            .all())
        elif treated == True:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.modifier_id.is_not(None))
            .offset(skip).limit(limit)
            .all())
        elif treated == False:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.modifier_id.is_(None))
            .offset(skip).limit(limit)
            .all())
        else:
            return (
                db.query(self.model)
                .join(Voice, Note.voice_id == Voice.id)
                .filter(Voice.doctor_id == doctor_id)
                .offset(skip).limit(limit)
                .all())
    
    def get_multi_by_doctor_id_count(self, db: Session, *, doctor_id: int, validated: Optional[bool]=None, treated: Optional[bool]=None) -> List[Note]:
        if type(validated) is bool and treated == True:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.validated == validated, Note.modifier_id.is_not(None))
            .count())

        elif type(validated) is bool and treated == False:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.validated == validated, Note.modifier_id.is_(None))
            .count())
        elif type(validated) is bool:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.validated == validated)
            .count())
        elif treated == True:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.modifier_id.is_not(None))
            .count())
        elif treated == False:
            return (
            db.query(self.model)
            .join(Voice, Note.voice_id == Voice.id)
            .filter(Voice.doctor_id == doctor_id, Note.modifier_id.is_(None))
            .count())
        else:
            return (
                db.query(self.model)
                .join(Voice, Note.voice_id == Voice.id)
                .filter(Voice.doctor_id == doctor_id)
                .count())

    def get_by_note_id(
        self, db: Session, *, id: int
    ) -> Note:
        return (
            db.query(self.model)
            .filter(Note.id == id)
            .first()
        )

    def get_by_note_plus_id(
        self, db: Session, *, id: int
    ) -> Any:

        note = (db.query(self.model)
        .filter_by(id = id)
        .first())

        voice = (db.query(Voice)
        .filter_by(id = note.voice_id)
        .first())

        doctor = db.query(User).filter(User.id == voice.doctor_id).first()
        patient = db.query(User).filter(User.id == voice.patient_id).first()

        note_plus = NotePlus(**note.__dict__, 
            doctor_fullname = doctor.full_name, patient_fullname = patient.full_name)
        return note_plus
    
    def get_by_voice_id(
        self, db: Session, *, id: int
    ) -> Note:
        return (
            db.query(self.model)
            .filter(Note.voice_id == id)
            .first()
        )
    
    def get_by_remarque_note_id(
        self, db: Session, *, id: int
    ) -> RemarqueNote:
        return (
            db.query(RemarqueNote)
            .filter(RemarqueNote.id == id)
            .first()
        )
    
    def get_remarques_by_note_id(
        self, db: Session, *, id: int, skip: int = 0, limit: int = 20
    ) -> List[RemarqueNote]:
        remarques = db.query(RemarqueNote).filter(RemarqueNote.note_id == id)\
        .order_by(RemarqueNote.date_creation.desc())\
        .offset(skip).limit(limit).all()
        return remarques
    
    def create_remarque_note(
        self, db: Session, *, obj_in: RemarqueNote, date_creation: datetime
    ) -> List[RemarqueNote]:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = RemarqueNote(**obj_in_data, date_creation = date_creation)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


    def get_by_voice_id(
        self, db: Session, *, id: int
    ) -> List[Note]:
        return (
            db.query(self.model)
            .filter(Note.voice_id == id)
            .first()
        )
    
    def get_many_by_voice_id(
        self, db: Session, *, id: int
    ) -> List[Note]:
        return (
            db.query(self.model)
            .filter(Note.voice_id == id)
            .all()
        )
    
    def get_multi_by_manager(
        self, db: Session, *, manager_id: int, validated: Optional[bool]=None, skip: int=0, limit: int = 5
    ) -> List[Note]:

        
        if type(validated) is bool:
            return (db.query(self.model)
            .join(AssistantManager, AssistantManager.assistant_id == Note.assistant_id)
            .filter(AssistantManager.manager_id == manager_id, Note.validated==validated)
            .offset(skip).limit(limit)
            .all()) 
        return (db.query(self.model)
            .join(AssistantManager, AssistantManager.assistant_id == Note.assistant_id)
            .filter(AssistantManager.manager_id == manager_id)
            .offset(skip).limit(limit)
            .all())
    
    def get_multi_by_manager_count(
        self, db: Session, *, manager_id: int, validated: Optional[bool]=None
    ) -> int:
        if type(validated) is bool:
            return (db.query(self.model)
            .join(AssistantManager, AssistantManager.assistant_id == Note.assistant_id)
            .filter(AssistantManager.manager_id == manager_id, Note.validated==validated)
            .count())
        if type(validated) is bool:
            return (db.query(self.model)
            .join(AssistantManager, AssistantManager.assistant_id == Note.assistant_id)
            .filter(AssistantManager.manager_id == manager_id, Note.validated==validated)
            .count())
        return (db.query(self.model)
            .join(AssistantManager, AssistantManager.assistant_id == Note.assistant_id)
            .filter(AssistantManager.manager_id == manager_id)
            .count())
    
    def get_multi_by_assistant(
        self, db: Session, *, assistant_id: int, validated: Optional[bool]=None, treated: Optional[bool]=None, skip: int=0, limit: int = 5
    ) -> List[Note]:
        if type(validated) is bool and treated == True:
            return (
            db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.validated==validated, Note.modifier_id.is_not(None))
            .offset(skip).limit(limit)
            .all())
        elif type(validated) is bool and treated == False:
            return (
            db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.validated==validated, Note.modifier_id.is_(None))
            .offset(skip).limit(limit)
            .all())
        elif type(validated) is bool:
            return (
            db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.validated==validated)
            .offset(skip).limit(limit)
            .all())
        elif treated == True:
            return (
            db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.modifier_id.is_not(None))
            .offset(skip).limit(limit)
            .all())
        elif treated == False:
            return (
            db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.modifier_id.is_(None))
            .offset(skip).limit(limit)
            .all())
        else:
            return (
                db.query(self.model)
                .filter(Note.assistant_id==assistant_id)
                .offset(skip).limit(limit)
                .all())
    
    def get_multi_by_assistant_count(
        self, db: Session, *, assistant_id: int, validated: Optional[bool]=None, treated: Optional[bool]=None
    ) -> int:
        if type(validated) is bool and treated == True:
            return (db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.validated==validated, Note.modifier_id.is_not(None))
            .count())
        elif type(validated) is bool and treated == False:
            return (db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.validated==validated, Note.modifier_id.is_(None))
            .count())
        elif type(validated) is bool:
            return (db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.validated==validated)
            .count())
        elif treated == True:
            return (
            db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.modifier_id.is_not(None))
            .count())
        elif treated == False:
            return (
            db.query(self.model)
            .filter(Note.assistant_id==assistant_id, Note.modifier_id.is_(None))
            .count())
        else:
            return (db.query(self.model)
                .filter(Note.assistant_id==assistant_id)
                .count())
    
    def get_multi_by_patient(
        self, db: Session, *, patient_id: int, validated: Optional[bool]=None, skip: int=0, limit: int = 5
    ) -> List[Note]:
        if type(validated) is bool:
            return (
            db.query(self.model)
            .join(Voice, Voice.id == Note.voice_id)
            .filter(Voice.patient_id==patient_id, Note.validated==validated)
            .offset(skip).limit(limit)
            .all())
        return (
            db.query(self.model)
            .join(Voice, Voice.id == Note.voice_id)
            .filter(Voice.patient_id==patient_id)
            .offset(skip).limit(limit)
            .all())
    
    def get_multi_by_patient_count(
        self, db: Session, *, patient_id: int, validated: Optional[bool]=None
    ) -> int:
        if type(validated) is bool:
            return (
            db.query(self.model)
            .join(Voice, Voice.id == Note.voice_id)
            .filter(Voice.patient_id==patient_id, Note.validated==validated)
            .count())
        return (
            db.query(self.model)
            .join(Voice, Voice.id == Note.voice_id)
            .filter(Voice.patient_id==patient_id)
            .count())
        
    def remove(self, db: Session, *, id: int) -> Note:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj




note = CRUDNote(Note)
