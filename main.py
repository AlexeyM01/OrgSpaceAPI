from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database import get_db, init_db
from src.models import Organization, Building, Activity

app = FastAPI()

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def handle_exception(e):
    return JSONResponse(status_code=500, content={"message": f"Произошла неизвестная ошибка: {e}"})


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/")
async def read_root():
    return {"message": "Hello World!"}
