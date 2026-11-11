import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from server.cache import SearchCache
from server.config import get_settings
from server.db import create_tables, make_engine, make_sessionmaker
from server.errors import ApiError
from server.providers.mock import MockProvider
from server.providers.sabre import SabreProvider
from server.routers import airports, flights
from server.schemas import HealthResponse

logger = logging.getLogger("server")

HTTP_STATUS_CODES = {404: "not_found", 405: "method_not_allowed", 429: "rate_limited"}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))
    app.state.http = client
    app.state.cache = SearchCache(timedelta(minutes=settings.search_ttl_minutes))
    app.state.provider = MockProvider() if settings.mock_enabled else SabreProvider(client, settings)
    engine = make_engine(settings.resolved_database_url)
    await create_tables(engine)
    app.state.db = make_sessionmaker(engine)
    logger.info("Flight provider: %s", app.state.provider.name)
    yield
    await client.aclose()
    await engine.dispose()


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def _readable_validation_message(exc: RequestValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()) if part not in ("body", "query", "path"))
        message = str(error.get("msg", "invalid value")).removeprefix("Value error, ")
        parts.append(f"{location}: {message}" if location else message)
    return "; ".join(parts) or "Invalid request"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Flights API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(400, "validation_error", _readable_validation_message(exc))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = HTTP_STATUS_CODES.get(exc.status_code, f"http_{exc.status_code}")
        return error_response(exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return error_response(500, "internal_error", "Unexpected server error")

    @app.get("/api/health", response_model=HealthResponse)
    async def health(request: Request) -> HealthResponse:
        return HealthResponse(status="ok", provider=request.app.state.provider.name)

    app.include_router(airports.router, prefix="/api")
    app.include_router(flights.router, prefix="/api")
    return app


app = create_app()
