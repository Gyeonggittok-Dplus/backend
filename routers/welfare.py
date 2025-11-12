from fastapi import APIRouter

# FastAPI Router object
router = APIRouter()

# Demo welfare dataset (UTF-8)
dummy_welfare = [
    {"id": 1, "title": "청년 주거 지원", "desc": "월세 최대 20만원 지원", "region": "경기도"},
    {"id": 2, "title": "노인 돌봄 서비스", "desc": "가정방문 돌봄 제공", "region": "수원시"},
    {"id": 3, "title": "저소득 의료비 지원", "desc": "연간 200만원 한도 지원", "region": "안양시"},
]


@router.get("/list")
def get_welfare_list():
    return {"welfare": dummy_welfare}


@router.get("/{welfare_id}")
def get_welfare_detail(welfare_id: int):
    result = next((item for item in dummy_welfare if item["id"] == welfare_id), None)
    if result:
        return result
    return {"error": "Not found"}

