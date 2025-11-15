# main.py
import os
import time
from uuid import uuid4
from typing import List, Optional, Dict, Any

from fastapi import APIRouter
from openai import OpenAI

from schemas.chat import ChatResponse, ChatRequest
from routers.welfare import get_welfare_list
from routers.auth import get_inform_fun
# ============================
# OpenAI 클라이언트
# ============================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# ※ 하드코딩된 키는 꼭 제거하고, 환경변수만 쓰는 걸 추천!

# ============================
# FastAPI 라우터
# ============================
router = APIRouter()

# ============================
# 세션 관리 (메모리 기반)
# ============================
SESSION_TTL = 300  # 5분

SESSIONS: Dict[str, Dict[str, Any]] = {}
# 구조:
# {
#   session_id: {
#       "messages": [ {role, content}, ... ],
#       "updated_at": float,
#   }
# }


def new_session_id() -> str:
    return str(uuid4())


def get_or_create_session(session_id: Optional[str]):
    now = time.time()

    # 1) 세션 없음 → 새로 생성
    if not session_id or session_id not in SESSIONS:
        sid = new_session_id()
        SESSIONS[sid] = {
            "messages": [],
            "updated_at": now,
        }
        return sid, SESSIONS[sid]

    session = SESSIONS[session_id]

    # 2) 5분 이상 대화 없음 → 히스토리 초기화
    if now - session["updated_at"] > SESSION_TTL:
        SESSIONS[session_id] = {
            "messages": [],
            "updated_at": now,
        }
        return session_id, SESSIONS[session_id]

    # 3) 정상 세션 → 시간만 갱신
    session["updated_at"] = now
    return session_id, session


# ============================
# 복지 DB 조회 래퍼
# ============================

def search_welfare_from_db(email: str):
    """
    email로 해당 유저의 location을 찾고,
    그 location에 해당하는 복지 리스트를 반환.
    routers.welfare.get_welfare_list를 그대로 재사용.
    """
    return get_welfare_list(email)


def welfare_rows_to_text(rows) -> str:
    """
    DB에서 가져온 rows(튜플 리스트)를
    GPT가 이해하기 쉬운 한국어 텍스트로 변환.
    (컬럼 순서를 tbwelfaressrsm SELECT 기준으로 가정)
    """
    if not rows:
        return "이 사용자의 지역에 등록된 복지 정보가 없습니다."

    lines: List[str] = []

    for row in rows[:20]:
        # row 는 RealDictRow → dict처럼 사용
        sigun_name = row["sigun_name"]
        service_name = row["service_name"]
        target = row["target"]
        support_cycle = row["support_cycle"]
        department = row["department"]
        apply_method = row["apply_method"]
        service_url = row["service_url"]

        line = (
            f"- [{sigun_name}] {service_name}\n"
            f"  · 대상: {target or '정보 없음'}\n"
            f"  · 지원 주기: {support_cycle or '정보 없음'}\n"
            f"  · 담당 부서: {department or '정보 없음'}\n"
            f"  · 신청 방법: {apply_method or '정보 없음'}\n"
            f"  · 링크: {service_url or '없음'}"
        )
        lines.append(line)
    return "\n".join(lines)


# ============================
# 엔드포인트 정의 (1-call GPT)
# ============================

@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    """
    메인 챗봇 엔드포인트 (1-call 버전).
    - session_id 없으면 새로 생성
    - 기존 세션이면 5분 TTL 체크 후 유지/초기화
    - email을 이용해 DB에서 복지 리스트를 한 번 조회하고,
      그 결과를 system 컨텍스트로 넣은 뒤 GPT를 1번만 호출
    """
    # 1) 세션 처리
    session_id, session = get_or_create_session(body.session_id)

    # 2) email 기반 복지 데이터 조회
    welfare_rows = []
    welfare_context_text = "사용자의 이메일이 없어서 지역 복지 정보를 조회할 수 없습니다. 일반적인 복지 안내만 제공하세요."
    if body.email:
        try:
            welfare_rows = search_welfare_from_db(body.email)
            welfare_context_text = (
                "다음은 사용자의 거주 지역(location)에 기반하여 조회된 복지 정보 목록입니다.\n"
                "이 정보를 적극적으로 참고해서 사용자의 질문에 맞는 복지 정보를 골라 설명하세요.\n\n"
                f"{welfare_rows_to_text(welfare_rows)}"
            )
        except Exception as e:
            # DB 오류가 나도 챗봇은 동작하게
            welfare_context_text = (
                f"지역 복지 정보를 조회하는 중 오류가 발생했습니다({e}). "
                "대신 한국의 일반적인 복지 제도에 대해 안내하세요."
            )

    # 3) GPT에 보낼 메시지 구성 (한 번만 호출)
    messages: List[Dict[str, str]] = []

    # 기존 대화 히스토리
    messages.extend(session["messages"])

    # 시스템 역할: 봇 성격 + 복지 데이터 컨텍스트
    messages.append({
        "role": "system",
        "content": (
            "너는 한국 사용자를 돕는 복지 안내 챗봇이야. "
            "항상 한국어로 친절하고 이해하기 쉽게 답변해."
        ),
    })
    messages.append({
        "role": "system",
        "content": welfare_context_text,
    })
    info = get_inform_fun(body.email)['user']

    user_profile_text = (
        f"사용자 기본 정보:\n"
        f"- 이메일: {info['email']}\n"
        f"- 지역: {info['location']}\n"
        f"- 나이: {info['age']}\n"
        f"- 성별: {info['sex']}\n"
    )
    messages.append({
        "role": "system",
        "content": user_profile_text,
    },)

    # 유저의 최신 질문
    messages.append({
        "role": "user",
        "content": body.message,
    })

    # 4) GPT 한 번 호출
    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # 비용 아끼려면 gpt-4o-mini 추천
        messages=messages,
    )
    reply = completion.choices[0].message.content or ""

    # 5) 세션 히스토리에 저장
    session["messages"].append({"role": "user", "content": body.message})
    session["messages"].append({"role": "assistant", "content": reply})

    return ChatResponse(session_id=session_id, reply=reply)
