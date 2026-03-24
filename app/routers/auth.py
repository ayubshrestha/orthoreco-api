from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserOut, Token, UserCreateByAdmin
from app.auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_current_user,
    require_roles,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing_patient_id = db.query(User).filter(User.patient_id == user.patient_id).first()
    if existing_patient_id:
        raise HTTPException(status_code=400, detail="Patient ID already exists")

    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        gender=user.gender,
        date_of_birth=user.date_of_birth,
        patient_id=user.patient_id,
        email=user.email,
        password_hash=hash_password(user.password),
        surgery_type=user.surgery_type,
        surgery_side=user.surgery_side,
        surgery_date=user.surgery_date,
        role="patient",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/create-user", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user: UserCreateByAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    existing_patient_id = db.query(User).filter(User.patient_id == user.patient_id).first()
    if existing_patient_id:
        raise HTTPException(status_code=400, detail="Patient ID already exists")

    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        patient_id=user.patient_id,
        email=user.email,
        password_hash=hash_password(user.password),
        surgery_type=user.surgery_type,
        surgery_side=user.surgery_side,
        role=user.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # form_data.username will contain the email
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role,
            "patient_id": user.patient_id,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user