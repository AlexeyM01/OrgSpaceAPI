from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database import get_db, init_db
from src.models import Organization, Building, Activity, OrganizationActivity

app = FastAPI()

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def handle_exception(e):
    return JSONResponse(status_code=500, content={"message": f"Произошла неизвестная ошибка: {e}"})


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/organizations/by_building_address/",
         description="Получает организации, связанные с указанным адресом здания")
async def get_organizations_by_building_address(address: str, db: AsyncSession = Depends(get_db)):
    try:
        building_query = select(Building).where(Building.address == address)
        result = await db.execute(building_query)
        building = result.scalars().first()
        if not building:
            return JSONResponse(status_code=404, content={"message": "Здание не найдено"})

        organizations_query = select(Organization).where(Organization.building_id == building.id)
        organizations_result = await db.execute(organizations_query)
        organizations = organizations_result.scalars().all()
        if not organizations:
            return JSONResponse(status_code=404, content={"message": "Организация не найдена"})

        return {"organizations": [org.name for org in organizations]}
    except Exception as e:
        return handle_exception(e)


@app.get("/organizations/by_activity_name/",
         description="Получает организации, связанные с указанным именем активности.")
async def get_organizations_by_activity_name(activity_name: str, db: AsyncSession = Depends(get_db)):
    try:
        activity_query = select(Activity).where(Activity.name == activity_name)
        activity_result = await db.execute(activity_query)
        activity = activity_result.scalars().first()
        if not activity:
            return JSONResponse(status_code=404, content={"message": "Активность не найдена"})

        organizations_query = select(OrganizationActivity).where(OrganizationActivity.activity_id == activity.id)
        organizations_result = await db.execute(organizations_query)
        organizations = organizations_result.scalars().all()

        return {"organizations": [org.organization.name for org in organizations]}
    except Exception as e:
        return handle_exception(e)