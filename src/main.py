import logging
import sys

import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.logging import LoggingIntegration

import app.router as app_router_module
import auth.router as auth_router_module
import calorie.router as calorie_router_module
import social.router as social_router_module
import setting.router as setting_router_module
from config import settings
from config.containers import Container
from models import (
    ErrorResponseDTO,
    MessageErrorResponseDTO,
    PydanticErrorResponseDTO,
)
from utils import PydanticConvertor

app = FastAPI(
    title="Main service",
    responses={
        401: {"model": ErrorResponseDTO[MessageErrorResponseDTO]},
        422: {"model": ErrorResponseDTO[PydanticErrorResponseDTO]},
    },
)

if settings.production:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            )
        ],
        enable_logs=True,
    )

container = Container()
container.wire(
    modules=[
        sys.modules[__name__],
        auth_router_module,
        app_router_module,
        calorie_router_module,
        setting_router_module,
        "config.dependencies",
        social_router_module,
    ]
)
app.container = container

ORIGINS = {"*"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError):
    errors = PydanticConvertor().convert_errors(exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"error": {"errors": errors}}),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"error": {"message": exc.detail}}),
    )


app.include_router(auth_router_module.router)
app.include_router(social_router_module.router)
app.include_router(app_router_module.router)
app.include_router(calorie_router_module.router)
app.include_router(setting_router_module.router)
