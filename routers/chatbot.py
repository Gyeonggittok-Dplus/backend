from fastapi import APIRouter

router = APIRouter()


@router.post("/query")
def chatbot_query(data: dict):
    """Simple placeholder chatbot endpoint.

    Expects: {"message": string}
    Returns: {"reply": string}
    """
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return {"reply": "무엇을 도와드릴까요? 복지 관련 질문을 입력해 주세요."}

    # Very naive demo logic; replace with real LLM pipeline later
    if "주거" in user_msg:
        return {"reply": "경기도 주거 지원 사업이 있어요. 월세 최대 20만원을 지원합니다."}

    return {"reply": f"'{user_msg}'에 대한 정보를 아직 찾지 못했어요."}

