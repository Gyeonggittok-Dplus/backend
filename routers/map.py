# routes/gyeonggi.py
import os
import httpx

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from schemas.map import Facility, FacilityResponse
import psycopg2
from psycopg2.extras import RealDictCursor

DB_DSN = os.getenv("DATABASE_URL")
router = APIRouter()

def get_db_connection():
    conn = psycopg2.connect(DB_DSN
                            ,cursor_factory=RealDictCursor)
    return conn
def get_user_location_by_email(email: str) -> str | None:
    """
    userinform 테이블에서 email이 같은 행의 location 컬럼을 반환.
    없으면 None.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT location FROM userinform WHERE email = %s LIMIT 1",
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return row["location"]  # RealDictCursor라 키로 접근 가능
    finally:
        conn.close()


# =======================
# 라우트
# =======================

@router.get("/facilities", response_model=FacilityResponse)
async def get_gyeonggi_facilities(email: str):
    """
    유저 email만 받고, 경기도 공공데이터 API에서 시설 목록을 조회.
    """

    API_URL = "https://openapi.gg.go.kr/Ggresidewelfareinst"  # 실제 API 종류에 맞게 수정

    API_KEY = os.getenv("GYEONGGI_OPENAPI_KEY")
    SIGUN_NM = get_user_location_by_email(email)

    params = {
        "Key": API_KEY,
        "Type": "json",  # <-- JSON을 직접 받음
        "pIndex": 1,
        "pSize": 1000,
        "SIGUN_NM" : SIGUN_NM
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(API_URL, params=params)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail="Failed to fetch Gyeonggi API"
        )

    json_data = resp.json()
    # JSON 구조에 따라 row 목록 추출
    child  = json_data.get("Ggresidewelfareinst", [])
    rows = next(
        (v.get("row", []) for v in child if isinstance(v, dict) and "row" in v),
        []
    )
    facilities = []
    for row in rows:
        try:
            lat = float(row.get("REFINE_WGS84_LAT"))
            lng = float(row.get("REFINE_WGS84_LOGT"))
        except:
            continue

        facilities.append(
            Facility(
                name=row.get("INST_NM"),
                phone=row.get("TELNO"),
                lot_addr=row.get("REFINE_LOTNO_ADDR"),
                road_addr=row.get("REFINE_ROADNM_ADDR"),
                lo_addr = row.get("HMPG_URL"),
                lat=lat,
                lng=lng,
            )
        )

    return FacilityResponse(
        code=200,
        message="SUCCESS",
        data=facilities,
        user_location = SIGUN_NM
    )
