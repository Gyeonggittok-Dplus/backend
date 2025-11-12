import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

try:
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests
except Exception:  # optional at dev time; real env will install deps
    google_id_token = None
    google_requests = None

try:
    import jwt
except Exception:
    jwt = None

router = APIRouter()
logger = logging.getLogger(__name__)


class GoogleVerifyBody(BaseModel):
    id_token: str


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

    secret = os.getenv("JWT_SECRET", "dev-secret")
    token = jwt.encode({**payload}, secret, algorithm="HS256")

    return {"access_token": token, "token_type": "bearer", "user": payload}
