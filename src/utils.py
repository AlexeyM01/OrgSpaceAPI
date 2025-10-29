"""
src/utils.py
"""

from fastapi import Header, HTTPException, status

from src.config import API_KEY


def handle_exception(e):
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Произошла неизвестная ошибка: {e}")


async def verify_api_key(x_api_key: str = Header(...)) -> bool:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Невалидный ключ AP")
    return True
