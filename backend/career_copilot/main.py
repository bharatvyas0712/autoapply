from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from repository import init_db
from routes import router

app = FastAPI(
    title="AutoJobApply - Career Copilot Suite",
    description="Career mentor, Resume optimizer, ATS score checker, and Mock interview simulation platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health():
    return {"success": True, "message": "Career Copilot running ✅"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.AGENT_PORT, reload=False)
