from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env", override=False)
from routers import welfare, chatbot, alert, auth, map, user_inform
app = FastAPI(title="GyeonggiD+ Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(welfare.router, prefix="/api/welfare", tags=["Welfare"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(alert.router, prefix="/api/alert", tags=["Alert"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(map.router, prefix="/api/map",tags=["Map"])
app.include_router(user_inform.router, prefix="/api/inform",tags=["Inform"])


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.get("/api/health")
def api_health():
    """Standardized health endpoint for load balancers / uptime checks."""
    return {"status": "ok"}
