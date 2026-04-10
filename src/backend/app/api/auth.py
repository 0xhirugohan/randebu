from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Annotated

from ..core.database import get_db
from ..core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_token,
)
from ..core.config import get_settings
from ..core.limiter import limiter
from ..db.schemas import (
    UserCreate,
    LoginRequest,
    UserResponse,
    Token,
    UserSettings,
    UserSettingsUpdate,
)
from ..db.models import User

router = APIRouter()
settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

TOKEN_BLACKLIST = set()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> User:
    if token in TOKEN_BLACKLIST:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@router.post(
    "/register", response_model=Token, status_code=status.HTTP_201_CREATED
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        password_hash=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Generate and return access token so frontend can proceed immediately
    access_token = create_access_token(data={"sub": db_user.id})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[str, Depends(oauth2_scheme)],
):
    TOKEN_BLACKLIST.add(token)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.get("/settings", response_model=UserSettings)
def get_settings_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return UserSettings(email=current_user.email)


@router.patch("/settings", response_model=UserSettings)
def update_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    settings_update: UserSettingsUpdate,
    db: Session = Depends(get_db),
):
    if settings_update.email:
        existing = (
            db.query(User)
            .filter(User.email == settings_update.email, User.id != current_user.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        current_user.email = settings_update.email
    if settings_update.password:
        current_user.password_hash = get_password_hash(settings_update.password)
    db.commit()
    db.refresh(current_user)
    return UserSettings(email=current_user.email)
