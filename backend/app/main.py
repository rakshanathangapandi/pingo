from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.endpoints import (
    auth, reminders, requests, payments, assets,
    challenges, wheel, gifts, notifications, dashboard
)
from app.models import *  # Import all models for table creation


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(reminders.router, prefix=f"{settings.API_V1_STR}/reminders", tags=["reminders"])
app.include_router(requests.router, prefix=f"{settings.API_V1_STR}/requests", tags=["requests"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])
app.include_router(assets.router, prefix=f"{settings.API_V1_STR}/assets", tags=["assets"])
app.include_router(challenges.router, prefix=f"{settings.API_V1_STR}/challenges", tags=["challenges"])
app.include_router(wheel.router, prefix=f"{settings.API_V1_STR}/wheel", tags=["wheel"])
app.include_router(gifts.router, prefix=f"{settings.API_V1_STR}/gifts", tags=["gifts"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
def root():
    return {"message": "Welcome to Pingo Admin Management Dashboard API"}