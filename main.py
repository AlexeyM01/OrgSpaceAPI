"""
main.py
"""

from fastapi import FastAPI
import logging


from src.database import init_db
from src.api.activities import router as activities_router
from src.api.buildings import router as buildings_router
from src.api.organizations import router as organizations_router


app = FastAPI()

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

app.include_router(activities_router)
app.include_router(buildings_router)
app.include_router(organizations_router)


@app.on_event("startup")
async def startup_event():
    await init_db()
