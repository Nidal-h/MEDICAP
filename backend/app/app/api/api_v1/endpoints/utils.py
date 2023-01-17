from typing import Any

from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app import models, schemas
from app.api import deps
from app import crud
from app.utils import send_test_email, send_notification, send_notification_firebase

from uuid import uuid4

from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/test-email/", response_model=schemas.Msg, status_code=201)
def test_email(
    email_to: EmailStr,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Test emails.
    """
    send_test_email(email_to=email_to)
    return {"msg": "Test email sent"}

@router.post("/test-send-notification/", status_code=201)
def test_notification(
    msg_title: str,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Test emails.
    """
    # Using pusher
    #if not current_user.uuid:
    #    current_user = crud.user.update(db=db, db_obj=current_user, obj_in=dict({'uuid':uuid4()}))
    #response = send_notification(msg=msg, to_users=[current_user.uuid], to_topics=[])
    
    # using firebase
    if current_user.firebase_device_token:
        result = send_notification_firebase(
            msg_title= msg_title, msg_body= {'user_id': current_user.id},\
                to_users=[current_user.firebase_device_token])
    else:
        result = 'firebase_device_token is none' 

    return result
