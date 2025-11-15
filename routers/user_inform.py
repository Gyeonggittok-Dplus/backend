import logging
from typing import Optional

from fastapi import APIRouter
import os
import psycopg2

router = APIRouter()
db_url = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(
        db_url
    )


@router.post("/post_fav_welfare")
def post_fav_welfare(email: str, welfare: str, url: str):
    combined_value = f"{welfare},{url}"

    conn = get_connection()
    cur = conn.cursor()

    # 1) 이미 email이 있는지 확인
    cur.execute("SELECT welfare FROM userfavwelfare WHERE email = %s", (email,))
    result = cur.fetchone()

    if result:
        # 이미 email 존재 → welfare 배열에 append
        update_query = """
            UPDATE userfavwelfare
            SET welfare = array_append(welfare, %s)
            WHERE email = %s
        """
        cur.execute(update_query, (combined_value, email))
    else:
        # email 없음 → 새로운 행 추가 (배열로 첫 값 넣기)
        insert_query = """
            INSERT INTO userfavwelfare (email, welfare)
            VALUES (%s, ARRAY[%s])
        """
        cur.execute(insert_query, (email, combined_value))

    conn.commit()
    cur.close()
    conn.close()

    return {"success": True, "message": "Favorites updated successfully"}

@router.get("/get_fav_welfare")
def get_fav_welfare(email: str):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT welfare 
        FROM userfavwelfare
        WHERE email = %s
    """
    cur.execute(query, (email,))
    result = cur.fetchone()

    cur.close()
    conn.close()

    # email이 없을 경우
    if not result:
        return {
            "success": False,
            "message": "User not found",
            "welfare": []
        }

    welfare_list = result[0]  # TEXT[]가 리스트로 그대로 들어감

    return {
        "success": True,
        "email": email,
        "welfare": welfare_list
    }
@router.post("/rm_fav_welfare")
def rm_fav_welfare(email: str, welfare: str, url: str):
    combined_value = f"{welfare},{url}"

    conn = get_connection()
    cur = conn.cursor()

    # 1) 해당 email 존재 여부 확인
    cur.execute("SELECT welfare FROM userfavwelfare WHERE email = %s", (email,))
    result = cur.fetchone()

    if not result:
        cur.close()
        conn.close()
        return {"success": False, "message": "User not found"}

    # 2) welfare 배열에서 값 제거 + 제거 후 배열 상태 반환
    update_query = """
        UPDATE userfavwelfare
        SET welfare = array_remove(welfare, %s)
        WHERE email = %s
        RETURNING welfare;
    """
    cur.execute(update_query, (combined_value, email))
    updated = cur.fetchone()

    # 혹시 모를 안전 처리
    if not updated:
        cur.close()
        conn.close()
        return {
            "success": False,
            "message": "Update failed (no row updated)"
        }

    updated_welfare = updated[0]  # TEXT[] → 파이썬 리스트로 들어옴 (또는 None)

    # 3) 배열이 완전히 비면 row 삭제
    if not updated_welfare:  # None 이거나 빈 리스트인 경우 둘 다 포함
        delete_query = "DELETE FROM userfavwelfare WHERE email = %s"
        cur.execute(delete_query, (email,))
        conn.commit()
        cur.close()
        conn.close()
        return {
            "success": True,
            "message": "Favorite welfare removed and row deleted (no more favorites)",
            "removed": combined_value,
            "row_deleted": True
        }

    # 4) 배열이 아직 남아 있으면 row는 유지
    conn.commit()
    cur.close()
    conn.close()

    return {
        "success": True,
        "message": "Favorite welfare removed",
        "removed": combined_value,
        "row_deleted": False,
        "current_welfare": updated_welfare
    }

@router.post("/update_inform")
def update_inform(
    email: str,
    location: Optional[str] = None,
    sex: Optional[str] = None,
    age: Optional[int] = None
):
    conn = get_connection()
    cur = conn.cursor()

    # 1) 해당 email 존재하는지 확인
    cur.execute("SELECT 1 FROM userinform WHERE email = %s", (email,))
    exists = cur.fetchone()

    if not exists:
        cur.close()
        conn.close()
        return {"success": False, "message": "User not found"}

    # 2) 업데이트할 필드만 동적 생성
    update_fields = []
    update_values = []

    if location is not None:
        update_fields.append("location = %s")
        update_values.append(location)

    if sex is not None:
        update_fields.append("sex = %s")
        update_values.append(sex)

    if age is not None:
        update_fields.append("age = %s")
        update_values.append(age)

    # 업데이트할 필드가 아무것도 없으면 실행 X
    if not update_fields:
        cur.close()
        conn.close()
        return {"success": False, "message": "No fields to update"}

    # 동적으로 UPDATE SQL 생성
    update_query = f"""
        UPDATE userinform
        SET {', '.join(update_fields)}
        WHERE email = %s
    """

    update_values.append(email)  # 마지막에 email 추가 (WHERE)
    cur.execute(update_query, tuple(update_values))
    conn.commit()

    # 3) 업데이트 후 최신 정보 조회
    cur.execute(
        "SELECT email, location, sex, age FROM userinform WHERE email = %s",
        (email,)
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    return {
        "success": True,
        "message": "User info updated",
        "user": {
            "email": row[0],
            "location": row[1],
            "sex": row[2],
            "age": row[3],
        }
    }
