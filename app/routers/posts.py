from fastapi import status, HTTPException, Depends, APIRouter, Response
from sqlalchemy import select, cast, Integer, update, Boolean, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, oauth2, utils
from app.db.models import User, Vote, Post
from app.db.session import get_async_session
from app.repositories.posts import PostRepository

router = APIRouter(
    prefix='/posts',
    tags=['Posts']
)


@router.post("", status_code=status.HTTP_201_CREATED,
             description='Create a new post',
             response_model=schemas.PostResponse)
async def create_post(post: schemas.PostCreate,
                      post_repo: PostRepository = Depends(),
                      current_user: User = Depends(oauth2.get_current_user)):
    new_post = await post_repo.post(post, current_user.uuid)
    return new_post


@router.get("/{post_id}",
            description='Get post with provided id',
            response_model=schemas.PostResponse)
async def get_post(post_id: int, post_repo: PostRepository = Depends()):
    post = await post_repo.get(post_id)

    return post


@router.get("",
            description='Get paginated list of posts',
            response_model=list[schemas.PostResponse])
async def get_all_published_posts(page: int = 1,
                                  post_repo: PostRepository = Depends()):
    posts = await post_repo.get_all_paginated(page)

    return posts


@router.put("/{post_id}",
            description='Update a post. Only for author of the post',
            response_model=schemas.PostResponse)
async def update_post(post_id: int,
                      post: schemas.PostUpdate,
                      post_repo: PostRepository = Depends(),
                      current_user: User = Depends(oauth2.get_current_user)):
    updated_post = await post_repo.update(post_id, post, current_user.uuid)
    return updated_post


@router.delete("/{post_id}",
               description='Delete a post. Only for author of the post.')
async def delete_post(post_id: int,
                      post_repo: PostRepository = Depends(),
                      current_user: User = Depends(oauth2.get_current_user)):
    await post_repo.delete(post_id, current_user.uuid)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/vote',
             description='Like/dislike a post. Boolean is_like set to true '
                         'is like, otherwise - dislike')
async def like_post(post_id: int,
                    is_like: bool,
                    db: AsyncSession = Depends(get_async_session),
                    current_user: User = Depends(oauth2.get_current_user)):

    utils.check_int_value(post_id)

    post_stmt = select(Post).filter(Post.id == post_id)
    post = (await db.execute(post_stmt)).scalar()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The post with id: {post_id} not found")
    if post.author_id == current_user.uuid:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"You cannot {'dis' if not is_like else ''}like your own posts")

    await utils.change_redis_on_vote(post_id, current_user.uuid, is_like, db)

    vote = Vote(user_uuid=current_user.uuid, post_id=post_id, is_like=is_like)

    await db.merge(vote)
    await db.commit()

    return {'success': f'You have {"dis" if not is_like else ""}liked post with id: {post_id}'}
