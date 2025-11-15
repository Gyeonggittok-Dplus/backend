from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


def _get_conn():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def get_welfare_list(email: str) -> List[Dict[str, Any]]:
    """
    email 값을 이용해 userinform 테이블에서 location(=sigun_name)을 조회하고
    해당 지역의 복지 리스트를 반환한다.
    """

    # 1) 이메일 기반 사용자 지역 조회
    try:
        with _get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT location 
                FROM userinform 
                WHERE email = %(email)s
                """,
                {"email": email}
            )
            user = cur.fetchone()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if not user:
        raise HTTPException(status_code=404, detail="해당 이메일로 등록된 사용자를 찾을 수 없습니다.")

    sigun_name = user["location"]    # location 칼럼

    # 2) welfare 조회
    sql = """
        SELECT
            sigun_name,
            service_name,
            target,
            support_cycle,
            department,
            apply_method,
            service_url
        FROM tbwelfaressrsm
        WHERE sigun_name = %(sigun_name)s
    """

    try:
        with _get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"sigun_name": sigun_name})
            rows = cur.fetchall()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return rows


@router.get("/list")
def list_welfare_services(
        email: str
) -> List[Dict[str, Any]]:
    return get_welfare_list(email)



# @router.get("/list/senior", response_model=List[WelfareService])
# @_map_errors
# def list_senior_services(
#     client: GyeonggiOpenAPIClient = Depends(get_gyeonggi_client),
# ) -> List[WelfareService]:
#     services = client.fetch_senior_services()
#     return services
#
#
# @router.get("/list/youth", response_model=List[WelfareService])
# @_map_errors
# def list_youth_services(
#     client: GyeonggiOpenAPIClient = Depends(get_gyeonggi_client),
# ) -> List[WelfareService]:
#     services = client.fetch_youth_services()
#     return services
#
#
# @router.get("/facilities", response_model=List[WelfareFacility])
# def list_welfare_facilities(
#         region: Optional[str] = Query(None, description="Optional city/county filter"),
# ) -> List[WelfareFacility]:
#     sql = """
#         SELECT
#             facility_id,
#             name,
#             category,
#             address,
#             region,
#             latitude,
#             longitude,
#             phone,
#             updated_at
#         FROM welfare_facilities
#     """
#     params: Dict[str, Any] = {}
#     if region:
#         sql += " WHERE region = %(region)s"
#         params["region"] = region
#
#     try:
#         with _get_conn() as conn, conn.cursor() as cur:
#             cur.execute(sql, params)
#             rows = cur.fetchall()
#     except psycopg2.Error as exc:
#         raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
#
#     return [WelfareFacility(**row) for row in rows]
#
#
# @router.get("/announcements", response_model=List[WelfareAnnouncement])
# def list_welfare_announcements(
#         region: Optional[str] = Query(None, description="Optional city/county filter"),
# ) -> List[WelfareAnnouncement]:
#     sql = """
#         SELECT
#             announcement_id,
#             title,
#             summary,
#             category,
#             apply_start_date,
#             apply_end_date,
#             region,
#             source_url
#         FROM welfare_announcements
#     """
#     params: Dict[str, Any] = {}
#     if region:
#         sql += " WHERE region = %(region)s"
#         params["region"] = region
#
#     try:
#         with _get_conn() as conn, conn.cursor() as cur:
#             cur.execute(sql, params)
#             rows = cur.fetchall()
#     except psycopg2.Error as exc:
#         raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
#
#     return [WelfareAnnouncement(**row) for row in rows]
