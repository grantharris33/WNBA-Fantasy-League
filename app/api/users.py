from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import UserCreate, UserOut
from app.core.database import get_db
from app.core.security import hash_password
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Annotated[Session, Depends(get_db)]):
    """
    Create a new user with hashed password
    """
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Create new user
    hashed_password = hash_password(user_in.password)
    db_user = User(email=user_in.email, hashed_password=hashed_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.get("/me", response_model=UserOut)
def read_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Get current user information
    """
    return current_user
