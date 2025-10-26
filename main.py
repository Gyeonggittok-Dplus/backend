from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정 (React 프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/ping")
def ping():
    return {"message": "pong"}

@app.post("/api/chat")
def chat(data: dict):
    user_input = data.get("message", "")
    return {"reply": f"'{user_input}'에 대한 복지 정보를 준비 중이에요!"}
