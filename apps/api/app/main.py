"""FastAPI application factory.

Single entrypoint that:
- configures structured logging
- mounts CORS + rate limiting
- mounts the v1 router
- wires lifespan hooks for db/redis
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import dispose_engine
from app.core.logging import configure_logging, get_logger
from app.core.redis_client import close_redis, get_redis

configure_logging()
log = get_logger("ptaa.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the connections so the first request is fast.
    await get_redis()
    log.info("api.startup", version=__version__, env=settings.APP_ENV)
    try:
        yield
    finally:
        log.info("api.shutdown")
        await close_redis()
        await dispose_engine()


def _key_func(request: Request) -> str:
    """Rate limit key — per-user when authenticated, per-IP otherwise."""
    user_id = getattr(request.state, "user_id", None)
    return user_id or get_remote_address(request)


limiter = Limiter(
    key_func=_key_func,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    headers_enabled=True,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=__version__,
        debug=settings.APP_DEBUG,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok", "version": __version__, "env": settings.APP_ENV}

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        log.error("api.unhandled", path=str(request.url), exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    app.include_router(api_router)
    return app


app = create_app()
