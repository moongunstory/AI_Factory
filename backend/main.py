# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Shorts Factory - Job Queue Mode", version="1.0.0")

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
def root():
    return {
        "message": "AI Shorts Factory - Job Queue Mode",
        "info": "브라우저 자동화는 별도 워커 프로세스에서 실행됩니다."
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

from backend.routers import job_router
app.include_router(job_router.router, prefix="/api", tags=["jobs"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
