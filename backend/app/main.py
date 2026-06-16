from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import ai_explanations, attempts, auth, board, daily, me, practice, settings
from backend.app.core.config import get_settings


def create_app() -> FastAPI:
    app_settings = get_settings()
    app = FastAPI(title=app_settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(daily.router)
    app.include_router(auth.router)
    app.include_router(practice.router)
    app.include_router(attempts.router)
    app.include_router(ai_explanations.router)
    app.include_router(board.router)
    app.include_router(me.router)
    app.include_router(settings.router)

    return app


app = create_app()
