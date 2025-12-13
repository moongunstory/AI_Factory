# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI(title="AI Shorts Factory Backend", version="0.1.0")

# CORS setup for Frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Shorts Factory Engine Online"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from routers import automation_router
app.include_router(automation_router.router, prefix="/api/automation", tags=["automation"])
# from backend.api.v1.endpoints import generation
# app.include_router(generation.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
