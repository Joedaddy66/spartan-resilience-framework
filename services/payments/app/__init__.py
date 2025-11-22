from fastapi import FastAPI
from .webhooks import router as webhook_router

def create_app() -> FastAPI:
    app = FastAPI(title="Payments Service")
    app.include_router(webhook_router, prefix="/api")
    return app

app = create_app()
