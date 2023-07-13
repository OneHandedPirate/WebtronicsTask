from uuid import UUID

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import select, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models, session
from app import schemas, utils


router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.post('', status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(session.get_async_session)):
    query = select(models.User).filter(models.User.email == cast(user.email, String))
    user_result = await db.execute(query)
    user_exists = user_result.scalars().first()

    if user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'The user with {user.email} is already registered')

    hashed_password = utils.hash_password(user.password)
    user.password = hashed_password

    new_user_dict = user.model_dump()

    new_user = models.User(**new_user_dict)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get('/{uuid}', response_model=schemas.UserResponse)
async def get_user(uuid: UUID,
                   db: AsyncSession = Depends(session.get_async_session)):
    query = select(models.User).filter(models.User.uuid == uuid)
    result = await db.execute(query)
    user = result.scalar()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The user with uuid {uuid} is not exist")

    return user



