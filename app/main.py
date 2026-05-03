import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, gait, dashboard, reports, appointments, notes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Orthoreco API",
    description="Research-grade gait and activity monitoring backend for orthopaedics",
    version="1.0.0",
)

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [
    o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(gait.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(appointments.router)
app.include_router(notes.router)

@app.get("/")
def root():
    return {"message": "Orthoreco backend is running"}


@app.get("/db-check")
def db_check():
    return {"status": "Database connected successfully"}