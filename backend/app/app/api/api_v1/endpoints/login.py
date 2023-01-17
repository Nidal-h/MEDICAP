from datetime import timedelta
from typing import Any, Union

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils import (
    generate_password_reset_token,
    send_reset_password_email,
    verify_password_reset_token,
    verify_confirmation_token,
)

router = APIRouter()


@router.post("/login/access-token", response_model=Union[schemas.Token, schemas.UserLoginOrCreationErr])
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        #raise HTTPException(status_code=400, detail={"error":"Incorrect email or password", "status_code" : 400})
        return schemas.UserLoginOrCreationErr(msg="Erreur de connexion, le nom d'utilisateur ou le mot de passe est erroné")
    elif not user.is_active:
        #raise HTTPException(status_code=402, detail={"error":"Inactive user", "status_code" : 402})
        return schemas.UserLoginOrCreationErr(msg='Erreur de connexion, compte non activé, vérifier votre email pour le lien de confirmation')
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}", response_model=schemas.Msg)
def recover_password(email: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Password Recovery
    """
    user = crud.user.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Password recovery email sent"}


@router.post("/reset-password/", response_model=schemas.Msg)
def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    return {"msg": "Password updated successfully"}

@router.get("/confirmation/")
def confirm_account(
    token: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Confirm account
    """
    email = verify_confirmation_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not user.is_active:
        user.is_active = True
        db.add(user)
        db.commit()
    print('user', user)
    return RedirectResponse(settings.SERVER_HOST_FRONT+'/#/email-confirmation/'+user.full_name+'/'+user.email+'/'+str(user.is_active).lower())

@router.get('/test_redirect/')
def redicect_test() -> Any:
    "test r"
    server_host = settings.SERVER_HOST
    api_version = settings.API_V1_STR
    link = f"{server_host}{api_version}/confirmation?token="
    print('api_version', link)
    return RedirectResponse(settings.SERVER_HOST_FRONT)
