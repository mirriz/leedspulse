from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import auth
import src.models as models
import src.database as database
from src.routers import incidents, analytics

# Create Tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="LeedsPulse API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(incidents.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "LeedsPulse API is Online"}