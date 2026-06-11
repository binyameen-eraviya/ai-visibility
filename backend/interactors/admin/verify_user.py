import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.user import User as UserDB
from backend.utils.schema.response import UserResponse, VerificationResponse
from backend.utils.custom_exceptions import NotFound as DataNotFoundException


async def call(db: AsyncSession, user_id: uuid.UUID, current_user) -> VerificationResponse:
    try:
        user = await UserDB.find_by_id(db, user_id)

        if user.verified_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already verified",
            )

        verified_user = await UserDB.verify(db, user_id)

        return VerificationResponse(
            message="User verified successfully",
            user=UserResponse(
                id=verified_user.id,
                name=verified_user.name,
                email=verified_user.email,
                role=verified_user.role,
                verified_at=verified_user.verified_at,
            ),
            verified_at=verified_user.verified_at,
            next_step="User can now log in",
        )
    except DataNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
