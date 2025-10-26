from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GyeonggiD-Plus API")

origins = [
    "https://gyeonggid-plus.vercel.app",
    "http://localhost:5173",
    "https://gyeonggid-plus-backend.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ health endpoint 추가
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "GyeonggiD-Plus", "version": "0.1.0"}

@app.get("/api/ping")
def ping():
    return {"message": "pong"}

@app.post("/api/chat")
def chat(data: dict):
    user_input = data.get("message", "")
    return {"reply": f"'{user_input}'에 대한 복지 정보를 준비 중이에요!"}
