from uuid import UUID

from fastapi import status, HTTPException, Depends, APIRouter
from sqlalchemy import select, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models, session
from app import schemas, utils
from app.repositories.user import UserRepository


router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.post('', status_code=status.HTTP_201_CREATED,
             description='Create a new user object (registration)',
             response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, user_repo: UserRepository = Depends()):
    new_user = await user_repo.post(user)
    return new_user


@router.get('', status_code=status.HTTP_200_OK,
            description='Get users list',
            response_model=list[schemas.UserResponse])
async def get_all_users(page: int = 1, user_repo: UserRepository = Depends()):
    users_list = await user_repo.get_all_paginated(page)
    return users_list



@router.get('/{uuid}', description='Get the specific User object by its uuid',
            response_model=schemas.UserResponse)
async def get_user_by_uuid(uuid: UUID, user_repo: UserRepository = Depends()):
    user = await user_repo.get(uuid)
    return user









