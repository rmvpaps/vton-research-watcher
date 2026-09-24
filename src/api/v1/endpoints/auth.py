from sqlmodel import Field, Session, SQLModel, create_engine, select,desc
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import Annotated
from shared import settings,get_session_dep
from shared.usermodels import User,UserInDB,Token,TokenData
import jwt
from fastapi import Depends, APIRouter, HTTPException, status, Response,Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel
import asyncio
import logging

STAGE=f"/{settings.STAGE_NAME }" if settings.STAGE_NAME  else ""

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session_dep)]

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7





password_hash = PasswordHash.recommended()

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{STAGE}/v1/token/form")
security_scheme = HTTPBearer(auto_error=False)



def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


async def get_user(session:AsyncSession, email: str):

    try:
        statement = select(UserInDB).where(UserInDB.email == email)
        result = await session.exec(statement)
        user = result.first()

        if user:
            return user
    except Exception as e:
        raise Exception(f"Error in get user {e}")
    return None


async def authenticate_user(session:AsyncSession, email: str, password: str):
    user = await get_user(session, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],session: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if not credentials or not credentials.credentials:
            raise credentials_exception
        token = credentials.credentials
        logging.info("Checking token sub")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            logging.error(f"Could not find sub {payload}")
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        logging.error(f"invalid token {token}")
        raise credentials_exception
    
    user = await get_user(session, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def process_auth(session,username,password)->Token:
    logging.info(f"login_for_access_token {username}")
    try:
        user = await authenticate_user(session, username, password)
    except Exception as db_error:
        logging.error(f"Database crash during authentication: {db_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database query failure."
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(
        data={"sub": user.email, "type":"access"}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_token(
            data={"sub": user.email, "type":"refresh"}, expires_delta=refresh_token_expires
        )

    
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")



async def process_refresh(session,refresToken)->Token:
    logging.info(f"token_for_access_token")
    try:
        payload = jwt.decode(refresToken, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
                
        user_email = payload.get("sub")
        logging.info(f"refresh for {user_email}")
        #TODO: update DB for the user and add new refreshtoken
            
        # Generate new pair
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_token(
            data={"sub": user_email, "type":"access"}, expires_delta=access_token_expires
        )
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = create_token(
                data={"sub": user_email, "type":"refresh"}, expires_delta=refresh_token_expires
            )

            
        return Token(access_token=access_token,refresh_token=refresh_token,  token_type="bearer")
            
    except jwt.JWTError:
        raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )




class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/token")
async def login_for_access_token_json(
    credentials: LoginRequest,
    session: SessionDep,
    response: Response
) -> Token:
    logging.info(f"JSON Login Handshake via Postman for: {credentials.username}")
    MyToken =  await process_auth(session, credentials.username, credentials.password)
    
    return MyToken


@router.post("/refresh-token")
async def refresh_token_for_access_token_json(
    session: SessionDep,
    request: Request, response: Response
) -> Token:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    MyToken =  await process_refresh(session, refresToken=refresh_token)
    
    return MyToken

    
@router.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


