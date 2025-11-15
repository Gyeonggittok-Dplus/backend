import logging
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


