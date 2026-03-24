from fastapi import FastAPI
from app.database import Base, engine
from app.routers import auth, gait, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Orthoreco API",
    description="Research-grade gait and activity monitoring backend for orthopaedics",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(gait.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"message": "Orthoreco backend is running"}


@app.get("/db-check")
def db_check():
    return {"status": "Database connected successfully"}