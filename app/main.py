from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Enable CORS (Allows your React Frontend on port 3000 to talk to Python on 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development ease
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router)

@app.get("/")
def root():
    return {"message": "Chord Aligner API is running (Lite Mode)"}