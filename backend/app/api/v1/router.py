from fastapi import APIRouter

from app.api.v1.routes import admin, ai, auth, comments, likes, me, posts, topics, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(me.router)
api_router.include_router(posts.router)
api_router.include_router(topics.router)
api_router.include_router(likes.router)
api_router.include_router(comments.router)
api_router.include_router(admin.router)
api_router.include_router(ai.router)
