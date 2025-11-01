from fastapi import FastAPI
from .health import router as health_router


def register_routers(app: FastAPI) -> None:
    routers = [health_router]
    for r in routers:
        app.include_router(r, prefix="/api")
