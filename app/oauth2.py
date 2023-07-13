from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import environ
from app import schemas
from app.db import models, session


oauth_scheme = OAuth2PasswordBearer(tokenUrl='login')


SECRET_KEY = environ.SK
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = environ.JWT_EXPIRATION_TIME


def create_access_token(data: dict):
    """Create a new JWT token"""

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str, credential_exception):
    """Verify JWT token"""

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        uuid: str = payload.get("uuid")

        if uuid is None:
            raise credential_exception
        token_data = schemas.TokenData(uuid=uuid)
    except JWTError:
        raise credential_exception

    return token_data


async def get_current_user(token: str = Depends(oauth_scheme),
                           db: AsyncSession = Depends(session.get_async_session)):
    """Verify JWT token and get current user from it"""

    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail=f'Could not validate credentials',
                                          headers={"WWW-Authenticate": "Bearer"})
    token = verify_access_token(token, credentials_exception)

    result = await db.execute(select(models.User).filter(models.User.uuid == token.uuid))
    user = result.scalar()

    return user
