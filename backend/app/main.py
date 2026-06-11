from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import attempts, board, daily
from backend.app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(daily.router)
    app.include_router(attempts.router)
    app.include_router(board.router)

    return app


app = create_app()
