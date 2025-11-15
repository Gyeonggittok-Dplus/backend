import logging
from fastapi import APIRouter, HTTPException

import os



from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
 # optional at dev time; real env will install deps
from schemas.user_inform import UserInformBody,GoogleVerifyBody


try:
    import jwt
except Exception:
    jwt = None

import psycopg2  # 👈 DB 연동 추가

router = APIRouter()
logger = logging.getLogger(__name__)


db_url = os.getenv("DATABASE_URL")


@router.post("/google/verify")
def google_verify(body: GoogleVerifyBody):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="Server misconfigured: GOOGLE_CLIENT_ID not set")

    if google_id_token is None or google_requests is None:
        raise HTTPException(status_code=500, detail="google-auth not installed")

    if jwt is None:
        raise HTTPException(status_code=500, detail="PyJWT not installed")

    try:
        info = google_id_token.verify_oauth2_token(body.id_token, google_requests.Request(), client_id)
    except Exception as e:
        logger.warning("Google token verification failed: %s", e, exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid Google ID token") from e
        
    token_aud = info.get("aud")
    if token_aud != client_id:
        logger.error("Google token aud mismatch. expected=%s received=%s", client_id, token_aud)
        raise HTTPException(status_code=401, detail="Invalid Google ID token")
    payload = {    
        "sub": info.get("sub"),
        "email": info.get("email"),
        "name": info.get("name"),
    }

    # ============================
    # ① Neon userinform에 사용자 저장
    # ============================
    email = payload.get("email")
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        logger.warning("DATABASE_URL not set; skipping userinform insert")
    elif not email:
        logger.warning("No email in Google token; skipping userinform insert")
    else:
        conn = None
        cur = None
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

            # email이 이미 있는지 확인
            cur.execute("SELECT 1 FROM userinform WHERE email = %s", (email,))
            exists = cur.fetchone()

            # 없으면 새로 INSERT (age/location/sex는 일단 빈 문자열)
            if not exists:
                cur.execute(
                    "INSERT INTO userinform (email, age, location, sex) VALUES (%s, %s, %s, %s)",
                    (email, 0, "", "")
                )
                conn.commit()
                cur.close()
                conn.close()
                secret = os.getenv("JWT_SECRET", "dev-secret")
                token = jwt.encode({**payload}, secret, algorithm="HS256")
                return {
                    "user": "new user",
                    "email": email,
                    "status": "created",
                    "access_token": token,
                    "token_type": "bearer"
                }


        except Exception as e:
            # DB 문제 때문에 로그인 자체를 막고 싶지 않으면, 여기서는 그냥 로그만 남김
            logger.error("Failed to upsert user in userinform: %s", e, exc_info=True)
            return {"error",e}
        finally:
            if cur is not None:
                try:
                    cur.close()
                except Exception:
                    pass
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ============================
    # ② 기존 JWT 발급 로직 그대로 유지
    # ============================
    secret = os.getenv("JWT_SECRET", "dev-secret")
    token = jwt.encode({**payload}, secret, algorithm="HS256")

    return {"access_token": token, "token_type": "bearer", "user": payload}


@router.post("/post_inform")
def post_inform(body: UserInformBody):

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # 1. 이메일 존재 확인
    cur.execute("SELECT 1 FROM userinform WHERE email = %s", (body.email,))
    result = cur.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="User with this email does not exist")


    # 2. 나이 / 지역 / 성별 업데이트
    cur.execute(
        """
        UPDATE userinform
        SET age = %s,
            location = %s,
            sex = %s
        WHERE email = %s
        """,
        (body.age, body.location, body.sex, body.email)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "code": 200,
        "message": "User info updated successfully",
    }

def get_inform_fun(email:str):
    database = psycopg2.connect(db_url)
    sql = """
                SELECT 
                email,
                location,
                age,
                sex
            FROM userinform
            WHERE email = %s
            LIMIT 1
            """

    try:
        with database as conn, conn.cursor() as cur:
            cur.execute(sql, (email,))
            row = cur.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="해당 이메일의 유저 정보를 찾을 수 없습니다.")

            # row 는 튜플이라 변환
            user = {
                "email": row[0],
                "location": row[1],
                "age": row[2],
                "sex": row[3],
            }

            return {"success": True, "user": user}

    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=f"DB 조회 오류: {exc}")
@router.get("/get_inform")
def get_inform(email:str):
    """
        userinform 테이블에서 email로 유저 정보를 조회하는 API
        """
    return get_inform_fun(email)



