from fastapi import APIRouter, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from typing import Annotated

from app.core.security import get_token
from app.core.limiter import limiter
from app.db.session import get_session
from app.schemas.auth_schema import SignInAuth
from app.services.auth_service import (
    sign_in,
    log_in,
    logout_account
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/sign", status_code=201)
@limiter.limit("5/minute")
async def sign(
    request: Request,
    dataIn: SignInAuth,
    session: Session = Depends(get_session)
): 
    return sign_in(dataIn, session)

@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    dataIn: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session)
):
    return log_in(response, dataIn, session)

@router.post("/logout")
async def logout(
    response: Response,
    token: Annotated[str, Depends(get_token)],
    session: Annotated[Session, Depends(get_session)]
): return logout_account(response, token, session)