"""
main.py
"""

from fastapi import FastAPI
from src.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

app = FastAPI()


@app.get("/")
def read_root():
    return {
        "DB Host": DB_HOST,
        "DB Port": DB_PORT,
        "DB Name": DB_NAME,
        "DB User": DB_USER,
    }
