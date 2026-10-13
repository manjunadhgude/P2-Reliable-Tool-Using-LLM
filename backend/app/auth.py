import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def issue_token(user: User) -> str:
    payload = _encode(json.dumps({"sub": user.id, "exp": int((datetime.now(timezone.utc) + timedelta(hours=12)).timestamp())}).encode())
    signature = _encode(hmac.new(settings.demo_signing_secret.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(401, detail={"code": "unauthenticated", "message": "Sign in with a demo role."})
    try:
        payload, signature = credentials.credentials.split(".", 1)
        expected = _encode(hmac.new(settings.demo_signing_secret.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("signature")
        decoded = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if decoded["exp"] < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("expired")
        user = db.scalar(select(User).where(User.id == decoded["sub"], User.active.is_(True)))
        if user is None:
            raise ValueError("user")
        return user
    except Exception as exc:
        raise HTTPException(401, detail={"code": "invalid_session", "message": "Your demo session is invalid or expired."}) from exc


def require_role(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, detail={"code": "forbidden", "message": "This role cannot perform that action."})
        return user
    return dependency
