from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import UserLogin
from backend.service.auth_handler import AuthHandler
from backend.database.models.user import User as UserDB
from backend.utils.schema.response import LoginResponse
from backend.utils.custom_exceptions import (
 NotFound as DataNotFoundException,
 Unauthorized as UserNotVerifiedException
)

async def call(db: AsyncSession, payload: UserLogin):
    try:
        payload.email = payload.email.lower()

        user = await UserDB.find_by_credentials(db, payload.email, payload.password)
        access_token = AuthHandler.generate_access_token({"sub": str(user.id)})

        return LoginResponse(user=user, access_token=access_token)

    except DataNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    except UserNotVerifiedException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not verified"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
