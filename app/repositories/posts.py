from fastapi import Depends, HTTPException
from sqlalchemy import select, cast, Integer, Boolean, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app import utils, schemas
from app.db.models import Post
from app.db.session import get_async_session
from app.repositories.base import BaseDBRepository
from environ import PER_PAGE


class PostRepository(BaseDBRepository):
    model = Post

    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def get(self, id: int):
        utils.check_int_value(id)

        stmt = select(Post).filter(Post.id == cast(id, Integer),
                                   Post.published == cast(True, Boolean))
        result = await self.session.execute(stmt)
        post = result.scalar()

        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Post with id: {id} not found')

        rating = await utils.get_post_rating(id, self.session)

        post_response = utils.post_to_response(post, rating)

        return post_response

    async def post(self, post: schemas.PostCreate, user_uuid):
        new_post = Post(author_id=user_uuid, **post.model_dump())
        self.session.add(new_post)
        await self.session.commit()
        await self.session.refresh(new_post)
        print(new_post)
        post_response = utils.post_to_response(new_post, 0)

        return post_response

    async def get_all_paginated(self, page):
        utils.check_int_value(page)
        if page < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid page number. Page number must "
                                       "be greater than or equal to 1.")

        stmt = select(Post).filter(
            Post.published == cast(True, Boolean)).offset((page - 1) * PER_PAGE).limit(PER_PAGE)

        result = await self.session.execute(stmt)
        posts = result.scalars()
        posts_response = []
        for post in posts:
            rating = await utils.get_post_rating(post.id, self.session)
            posts_response.append(utils.post_to_response(post, rating))

        return posts_response

    async def update(self, post_id, post, user_uuid):
        utils.check_int_value(post_id)

        stmt = select(Post).filter(Post.id == cast(post_id, Integer))

        result = await self.session.execute(stmt)
        post_to_update = result.scalar()

        if post_to_update is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Post with id: {post_id} does not exist')

        if post_to_update.author_id != user_uuid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f'Not authorized to perform requested action')

        stmt_to_update = update(Post).where(
            Post.id == cast(post_id, Integer)).values(title=post.title,
                                                      content=post.content,
                                                      published=post.published)

        await self.session.execute(stmt_to_update)
        await self.session.commit()

        after_update = await self.session.execute(stmt)
        updated_post = after_update.scalar()

        updated_post_res = utils.post_to_response(updated_post,
                                                  await utils.get_post_rating(updated_post.id, self.session))

        return updated_post_res

    async def delete(self, post_id, user_uuid):
        utils.check_int_value(post_id)

        stmt = select(Post).filter(Post.id == cast(post_id, Integer))
        result = await self.session.execute(stmt)
        post = result.scalar()

        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Post with id: {post_id} does not exist')

        if post.author_id != user_uuid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f'Not authorized to perform requested action')

        stmt_to_delete = delete(Post).filter(Post.id == cast(post_id, Integer))
        await self.session.execute(stmt_to_delete)
        await self.session.commit()
