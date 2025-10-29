from fastapi import Header, HTTPException
from starlette.responses import JSONResponse

from src.config import API_KEY


def handle_exception(e):
    return JSONResponse(status_code=500, content={"message": f"Произошла неизвестная ошибка: {e}"})


async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Невалидный ключ AP")
    return True
