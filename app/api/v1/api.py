from fastapi import APIRouter
from app.api.v1.endpoints import auth, signup

api_router = APIRouter()
api_router.include_router(auth.router, tags=["login"])
api_router.include_router(signup.router, tags=["signup"])

