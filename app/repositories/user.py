from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends

from app import schemas
from app.repositories.base import BaseDBRepository
from sqlalchemy import select, cast, String
from app.db.models import User
from app.db.session import get_async_session
from app import utils
from environ import PER_PAGE


class UserRepository(BaseDBRepository):
    model = User

    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def get(self, id: UUID):
        stmt = select(self.model).filter(self.model.uuid == id)
        result = await self.session.execute(stmt)
        user = result.scalar()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"The {self.model.__tablename__} with uuid {id} does not exist")
        return user

    async def post(self, user: schemas.UserCreate):
        stmt = select(self.model).filter(self.model.email == cast(user.email, String))
        user_result = await self.session.execute(stmt)
        user_exists = user_result.scalars().first()

        if user_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'The user with {user.email} is already registered')

        hashed_password = utils.hash_password(user.password)
        user.password = hashed_password

        new_user_dict = user.model_dump()

        new_user = self.model(**new_user_dict)

        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def get_all_paginated(self, page):
        stmt = select(self.model).offset((page - 1) * PER_PAGE).limit(PER_PAGE)
        result = await self.session.execute(stmt)
        users = result.scalars()

        return users

    async def update(self, id):
        raise NotImplementedError('Delete is not implemented')

    async def delete(self, id):
        raise NotImplementedError('Delete is not implemented')


