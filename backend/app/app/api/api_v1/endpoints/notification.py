from typing import Any, List, Optional, Union
from itertools import chain

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pusher_push_notifications import PushNotifications

from datetime import datetime
from app import crud, models, schemas
from app.api import deps

from app.models.doctor_manager import DoctorManager
from app.models.assistant_manager import AssistantManager
from app.models.doctor_patient import DoctorPatient
from app.models.user import User

from uuid import uuid4

router = APIRouter()


#@router.get("/me")
#def read_user_me(
#    *,
#    db: Session = Depends(deps.get_db),
#    current_user: models.User = Depends(deps.get_current_active_user),
#    beams_client: PushNotifications= Depends(deps.get_beam_pusher),
#) -> Any:
#    """
#    Get user_id beam pusher token.
#    """
#    if not current_user.uuid:
#        current_user = crud.user.update(db=db, db_obj=current_user, obj_in=dict({'uuid':uuid4()}))
#    return beams_client.generate_token(current_user.uuid)

@router.get("/device/{device_token_id}", response_model=schemas.User)
def push_token_user_me(
    *,
    db: Session = Depends(deps.get_db),
    device_token_id: str,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update current_user user firebase device token.
    """
    user = crud.user.update_user_device(db=db, id=current_user.id, token=device_token_id)
    return user

