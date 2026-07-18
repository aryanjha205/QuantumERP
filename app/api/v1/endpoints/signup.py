from datetime import datetime, timedelta
import random
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.crud import crud_user
from app.api import deps
from app.core import security
from app.core.config import settings
from app.schemas.user import User, UserCreate
from app.services.mail import send_otp_email

from app.models.user import PendingUser

router = APIRouter()

@router.post("/signup/request-otp")
def request_otp(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Step 1: Check if email already exists, generate a 6-digit OTP, send it via email,
    and save user registration details in database.
    """
    user = crud_user.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    
    # Check if a pending registration for this email already exists
    existing = db.query(PendingUser).filter(PendingUser.email == user_in.email).first()
    if existing:
        db.delete(existing)
        db.commit()

    # Create a new PendingUser record
    pending = PendingUser(
        email=user_in.email,
        full_name=user_in.full_name,
        password=user_in.password,
        role=user_in.role.value if hasattr(user_in.role, 'value') else user_in.role,
        otp=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(pending)
    db.commit()

    # Send email in background
    background_tasks.add_task(send_otp_email, user_in.email, otp)
    
    return {"message": "OTP sent successfully to your email"}

@router.post("/signup/verify-otp", response_model=User)
def verify_otp(
    otp: str,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Step 2: Validate the OTP. If valid, register the user into the database.
    """
    pending = db.query(PendingUser).filter(PendingUser.otp == otp).first()
    if not pending:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    if pending.expires_at < datetime.utcnow():
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    # Reconstruct user object and create in DB
    obj_in = UserCreate(
        email=pending.email,
        password=pending.password,
        full_name=pending.full_name,
        role=pending.role
    )
    
    user = crud_user.user.create(db, obj_in=obj_in)
    
    # Clean up from database
    db.delete(pending)
    db.commit()
    
    return user
