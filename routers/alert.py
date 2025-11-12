from fastapi import APIRouter

router = APIRouter()

dummy_alerts = [
    {
        "id": 1,
        "title": "이번 주 마감 복지 TOP3",
        "desc": "청년 주거안정 지원 접수가 곧 마감됩니다.",
        "type": "calendar",
    },
    {
        "id": 2,
        "title": "긴급 복지 문자발송",
        "desc": "저소득층 에너지 지원 신청이 열렸습니다.",
        "type": "sms",
    },
]


@router.get("/list")
def get_alerts():
    return {"alerts": dummy_alerts}


@router.post("/subscribe")
def subscribe_alert(channel: str):
    # TODO: 실제 Calendar/Twilio 연동 로직으로 교체
    return {"status": "subscribed", "channel": channel}

