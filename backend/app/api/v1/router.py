from fastapi import APIRouter

from app.api.v1.routes import auth, comments, likes, me, posts, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(me.router)
api_router.include_router(posts.router)
api_router.include_router(likes.router)
api_router.include_router(comments.router)
