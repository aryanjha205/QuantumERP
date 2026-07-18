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

router = APIRouter()

# In-memory store for pending signups (OTP -> registration data mapping)
# For production serverless environments, this can be written to Redis or a temporary DB table,
# but for standard deployment, a timed dict is perfect for demonstration.
pending_signups: Dict[str, Dict[str, Any]] = {}

@router.post("/signup/request-otp")
def request_otp(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Step 1: Check if email already exists, generate a 6-digit OTP, send it via email,
    and save user registration details in memory.
    """
    user = crud_user.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    
    # Store registration details temporarily (expires in 10 minutes)
    pending_signups[otp] = {
        "user_data": user_in.model_dump(),
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }

    # Clean up expired OTPs to prevent memory bloating
    expired_otps = [o for o, data in pending_signups.items() if data["expires_at"] < datetime.utcnow()]
    for o in expired_otps:
        pending_signups.pop(o, None)

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
    signup_data = pending_signups.get(otp)
    if not signup_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    if signup_data["expires_at"] < datetime.utcnow():
        pending_signups.pop(otp, None)
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    # Remove from memory store
    pending_signups.pop(otp, None)

    # Reconstruct user object and create in DB
    user_data = signup_data["user_data"]
    obj_in = UserCreate(**user_data)
    
    user = crud_user.user.create(db, obj_in=obj_in)
    return user
