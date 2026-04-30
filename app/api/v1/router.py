from fastapi import APIRouter

from app.api.v1 import chat, conversations, profiles

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(chat.router)
api_v1_router.include_router(conversations.router)
api_v1_router.include_router(profiles.router)
