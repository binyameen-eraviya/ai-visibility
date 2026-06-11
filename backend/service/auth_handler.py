import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.db import get_db
from backend.utils.constants import Constants
from backend.utils.enums import UserRole
from backend.database.models.user import User as UserDB
from backend.database.migrations.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
pwd_context = CryptContext(schemes=["bcrypt"])

class AuthHandler:
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def generate_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=int(Constants.TOKEN_EXPIRE_DAYS))

        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, key=Constants.SECRET_KEY, algorithm=Constants.ALGORITHM)

    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = jwt.decode(token, Constants.SECRET_KEY, algorithms=[Constants.ALGORITHM])
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise credentials_exception
            user_id = uuid.UUID(user_id_str)
        except Exception:
            raise credentials_exception

        try:
            user = await UserDB.find_by_id(db, user_id)
        except Exception:
            raise credentials_exception

        if not user.verified_at:
            raise credentials_exception
        return user

    async def get_current_admin(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = jwt.decode(token, Constants.SECRET_KEY, algorithms=[Constants.ALGORITHM])
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise credentials_exception
            user_id = uuid.UUID(user_id_str)
        except Exception:
            raise credentials_exception

        try:
            user = await UserDB.find_by_id(db, user_id)
        except Exception:
            raise credentials_exception

        if not user.verified_at or user.role == UserRole.USER:
            raise credentials_exception
        return user

    async def get_current_super_admin(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = jwt.decode(token, Constants.SECRET_KEY, algorithms=[Constants.ALGORITHM])
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise credentials_exception
            user_id = uuid.UUID(user_id_str)
        except Exception:
            raise credentials_exception

        try:
            user = await UserDB.find_by_id(db, user_id)
        except Exception:
            raise credentials_exception

        if not user.verified_at or user.role != UserRole.SUPER_ADMIN:
            raise credentials_exception
        return user
