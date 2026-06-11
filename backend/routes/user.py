from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.utils.schema.request import UserLogin, UserSignup, SignupVerify, PasswordResetRequest, PasswordReset
from backend.interactors.auth import user_login as user_login_interactor
from backend.interactors.auth import user_signup as user_signup_interactor
from backend.interactors.auth import user_verify_email as user_verify_email_interactor
from backend.interactors.auth import password_reset_request as password_reset_request_interactor
from backend.interactors.auth import password_reset_complete as password_reset_complete_interactor

router = APIRouter(prefix="/api", tags=["user"])

@router.post("/login")
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    return await user_login_interactor.call(db, payload)

@router.post("/signup")
async def signup(payload: UserSignup, db: AsyncSession = Depends(get_db)):
    return await user_signup_interactor.call(db, payload)

@router.post("/verify-email")
async def verify_email(payload: SignupVerify, db: AsyncSession = Depends(get_db)):
    return await user_verify_email_interactor.call(db, payload)

@router.post("/password-reset-request")
async def password_reset_request(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    return await password_reset_request_interactor.call(db, payload)

@router.post("/password-reset")
async def password_reset(payload: PasswordReset, db: AsyncSession = Depends(get_db)):
    return await password_reset_complete_interactor.call(db, payload)
