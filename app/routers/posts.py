from fastapi import status, HTTPException, Depends, APIRouter, Response
from sqlalchemy import select, cast, Integer, update, Boolean, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, oauth2, utils
from app.db.models import User, Vote, Post
from app.db.session import get_async_session

from environ import POSTS_PER_PAGE

router = APIRouter(
    prefix='/posts',
    tags=['Posts']
)

status.HTTP_400_BAD_REQUEST

@router.post("", status_code=status.HTTP_201_CREATED,
             description='Create a new post',
             response_model=schemas.PostResponse)
async def create_post(post: schemas.PostCreate,
                      db: AsyncSession = Depends(get_async_session),
                      current_user: User = Depends(oauth2.get_current_user)):
    new_post = Post(author_id=current_user.uuid, **post.model_dump())
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    post_response = utils.post_to_response(new_post, 0)

    return post_response


@router.get("/{post_id}",
            description='Get post with provided id',
            response_model=schemas.PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_async_session)):
    utils.check_int_value(post_id)

    stmt = select(Post).filter(Post.id == cast(post_id, Integer),
                               Post.published == cast(True, Boolean))
    result = await db.execute(stmt)
    post = result.scalar()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Post with id: {post_id} not found')

    rating = await utils.get_post_rating(post_id, db)

    post_response = utils.post_to_response(post, rating)

    return post_response


@router.get("",
            description='Get paginated list of posts',
            response_model=list[schemas.PostResponse])
async def get_all_published_posts(page: int = 1,
                                  db: AsyncSession = Depends(get_async_session)):
    utils.check_int_value(page)
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid page number. Page number must "
                                   "be greater than or equal to 1.")

    stmt = select(Post).filter(
        Post.published == cast(True, Boolean)).offset((page-1)*POSTS_PER_PAGE).limit(POSTS_PER_PAGE)

    result = await db.execute(stmt)
    posts = result.scalars()
    posts_response = []
    for post in posts:
        rating = await utils.get_post_rating(post.id, db)
        posts_response.append(utils.post_to_response(post, rating))

    return posts_response


@router.put("/{post_id}",
            description='Update a post. Only for author of the post',
            response_model=schemas.PostResponse)
async def update_post(post_id: int,
                      post: schemas.PostUpdate,
                      db: AsyncSession = Depends(get_async_session),
                      current_user: User = Depends(oauth2.get_current_user)):
    utils.check_int_value(post_id)

    stmt = select(Post).filter(Post.id == cast(post_id, Integer))

    result = await db.execute(stmt)
    post_to_update = result.scalar()

    if post_to_update is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Post with id: {post_id} does not exist')

    if post_to_update.author_id != current_user.uuid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'Not authorized to perform requested action')

    stmt_to_update = update(Post).where(
        Post.id == cast(post_id, Integer)).values(title=post.title,
                                                  content=post.content,
                                                  published=post.published)

    await db.execute(stmt_to_update)
    await db.commit()

    after_update = await db.execute(stmt)
    updated_post = after_update.scalar()

    return updated_post


@router.delete("/{post_id}",
               description='Delete a post. Only for author of the post.')
async def delete_post(post_id: int,
                      db: AsyncSession = Depends(get_async_session),
                      current_user: User = Depends(oauth2.get_current_user)):
    utils.check_int_value(post_id)

    stmt = select(Post).filter(Post.id == cast(post_id, Integer))
    result = await db.execute(stmt)
    post = result.scalar()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Post with id: {post_id} does not exist')

    if post.author_id != current_user.uuid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'Not authorized to perform requested action')

    stmt_to_delete = delete(Post).filter(Post.id == cast(post_id, Integer))
    await db.execute(stmt_to_delete)
    await db.commit()

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
