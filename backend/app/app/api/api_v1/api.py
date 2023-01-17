from fastapi import APIRouter

from app.api.api_v1.endpoints import login, users, utils, voices, notes, relationships, notification

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(relationships.router, prefix="/relationships", tags=["relationships"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(notification.router, prefix="/notification", tags=["notification"])
api_router.include_router(voices.router, prefix="/voices", tags=["voices"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
