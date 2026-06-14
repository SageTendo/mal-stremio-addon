from datetime import datetime, timedelta, timezone
from typing import Optional

from app.db.db import db_backend


def get_user(user_id: str) -> Optional[dict]:
    return db_backend.get_user(user_id)


def store_user(user_details: dict) -> bool:
    return db_backend.store_user(user_details)


def get_valid_user(user_id: str) -> tuple[dict, Optional[str]]:
    user = get_user(user_id)
    if not user:
        return {}, "No user found. Please re-login to MyAnimeList."

    if (
        not user.get("last_updated")
        or not user.get("expires_in")
        or not user.get("access_token")
        or not user.get("refresh_token")
    ):
        return {}, "Invalid MAL session. Please refresh or login again."

    expiration_date = user["last_updated"] + timedelta(seconds=user["expires_in"])
    if datetime.utcnow() > expiration_date:
        return {}, "MAL session expired. Please refresh or login again."
    return user, None
