from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy import select, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, utils, oauth2
from app.db import models
from app.db.session import get_async_session


router = APIRouter(tags=['Authentication'])


@router.post('/login', response_model=schemas.Token, description='Login for registered users')
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_async_session)):

    #Since OAuth2PasswordRequestForm uses username and password we compare email with username
    result = await db.execute(select(models.User).filter(
        models.User.email == cast(user_credentials.username, String)))
    user = result.scalar()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Invalid credentials')

    if not utils.verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Invalid credentials')

    # create a token
    access_token = oauth2.create_access_token(data={'uuid': str(user.uuid)})
    return {"access_token": access_token, 'token_type': "bearer"}
