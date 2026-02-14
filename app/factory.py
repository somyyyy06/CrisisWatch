from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

def create_app() -> FastAPI:
    app = FastAPI(title="CrisisWatch API", version="1.0.0")

    # ----------------------------
    # Static uploads
    UPLOAD_DIR = "uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

    # ----------------------------
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ----------------------------
    # Lazy imports (CRITICAL)
    from app.main import (
        get_db,
        signup,
        login,
        health,
        ws_incidents,
        feed_router,
        subscriptions,
        incidents,
    )

    app.include_router(feed_router)
    app.include_router(subscriptions.router)
    app.include_router(incidents.router)

    app.add_api_route("/auth/signup", signup, methods=["POST"])
    app.add_api_route("/auth/token", login, methods=["POST"])
    app.add_api_route("/health", health, methods=["GET"])
    app.add_api_websocket_route("/ws/incidents", ws_incidents)

    return app
