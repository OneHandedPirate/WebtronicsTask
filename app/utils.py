from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Vote, Post
from app.redis_conn import redis
from app.schemas import PostResponse


pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password to store it in db"""

    return pwd_context.hash(password)


def verify_password(plain_pass: str, hashed_pass: str) -> bool:
    """Check if the password provided is correct"""

    return pwd_context.verify(plain_pass, hashed_pass)


def check_int_value(value: int):
    """Verify that the value provided is a valid int"""

    if value > 2147483647:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"The value {value} is too large")


async def get_post_rating(post_id: int, db: AsyncSession) -> int:
    """Return post rating of a post from redis"""

    vote_result = await redis.get(f'vote:{post_id}:result')
    if vote_result:
        return vote_result
    else:
        return await sync_redis(post_id, db)


def post_to_response(post: Post, rating: int) -> PostResponse:
    """Convert Post object into PostResponse object"""

    post = PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        published=post.published,
        author_id=post.author_id,
        created_at=post.created_at,
        rating=rating
    )
    return post


async def sync_redis(post_id: int, db: AsyncSession):
    """Sync Votes table w/ post_id with redis and return rating of the post"""

    stmt = select(Vote).where(Vote.post_id == post_id)
    votes = (await db.execute(stmt)).scalars().all()
    if not votes:
        await redis.set(f'vote:{post_id}:result', 0)
        return 0

    rating = 0
    for vote in votes:
        rating += (1 if vote.is_like else -1)
        await redis.set(f'vote:{vote.post_id}:{vote.user_uuid}', 1 if vote.is_like else -1)
    await redis.set(f'vote:{post_id}:result', rating)

    return rating


async def change_redis_on_vote(post_id: int, user_uuid, is_like: bool, db: AsyncSession):
    """Ugly redis interactions on vote"""

    if not await redis.keys(f'vote:{post_id}:*'):
        await get_post_rating(post_id, db)

    vote_key = f'vote:{post_id}:{user_uuid}'
    votes_result = f'vote:{post_id}:result'

    vote_in_redis = await redis.get(vote_key)

    if not vote_in_redis:
        await (redis.set(vote_key, 1) if is_like is True else redis.set(vote_key, -1))
        await (redis.incr(votes_result) if is_like else redis.decr(votes_result))
    else:
        if int(vote_in_redis) == 1:
            if is_like:
                pass
            else:
                redis.set(vote_key, -1)
                redis.decr(votes_result)
        else:
            if not is_like:
                pass
            else:
                redis.set(vote_key, 1)
                redis.incr(votes_result)

