from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.health import router as health_router
from api.routes.profile_entities import router as profile_entities_router
from api.routes.profiles import router as profiles_router
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router, prefix=settings.api_v1_prefix, tags=["health"])
    app.include_router(profiles_router, prefix=f"{settings.api_v1_prefix}/profiles", tags=["profiles"])
    app.include_router(
        profile_entities_router,
        prefix=f"{settings.api_v1_prefix}/profiles",
        tags=["profile-entities"],
    )
    return app


app = create_app()


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version, "docs": f"{settings.api_v1_prefix}/docs"}
