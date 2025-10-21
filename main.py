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


@app.get("/organizations/by_area/",
         description="Получает здания, расположенные в указанной области")
async def get_organizations_by_area(latitude: float, longitude: float, lat_diff: float, lon_diff: float,
                                    db: AsyncSession = Depends(get_db)):
    try:
        min_latitude = latitude - lat_diff
        max_latitude = latitude + lat_diff
        min_longitude = longitude - lon_diff
        max_longitude = longitude + lon_diff

        query = select(Building).where(
            Building.latitude.between(min_latitude, max_latitude),
            Building.longitude.between(min_longitude, max_longitude)
        )
        result = await db.execute(query)
        buildings = result.scalars().all()

        return {"buildings": [{"id": b.id, "address": b.address} for b in buildings]}
    except Exception as e:
        return handle_exception(e)


@app.get("/organization/{org_id}/", description="Получает детали организации по ID")
async def get_organization(org_id: int, db: AsyncSession = Depends(get_db)):
    try:
        organization_query = select(Organization).where(Organization.id == org_id)
        result = await db.execute(organization_query)
        organization = result.scalars().first()
        if not organization:
            return JSONResponse(status_code=404, content={"message": "Организация не найдена"})

        address_query = select(Building).where(Building.id == organization.building_id)
        address_result = await db.execute(address_query)
        address = address_result.scalars().first()

        return {
            "id": organization.id,
            "name": organization.name,
            "address": address.address if address else None,
            "phone_numbers": [pn.number for pn in organization.phone_numbers]
        }
    except Exception as e:
        return handle_exception(e)


@app.get("/organizations/search_by_activity/")
async def search_organizations_by_activity(activity_name: str, db: AsyncSession = Depends(get_db)):
    activities_to_search = []

    async def find_subactivities(activity, level):
        if activity:
            activities_to_search.append(activity)
            query = select(Activity).where(Activity.parent_id == activity.id)
            sub_activities = await db.execute(query)
            sub_activities_list = sub_activities.scalars().all()
            if level <= 3:
                for sub_activity in sub_activities_list:
                    await find_subactivities(sub_activity, level + 1)

    try:
        root_query = select(Activity).where(Activity.name == activity_name)
        root_result = await db.execute(root_query)
        root_activity = root_result.scalars().first()

        if root_activity:
            await find_subactivities(root_activity, 1)

        organizations = set()
        for activity in activities_to_search:
            query = select(OrganizationActivity).where(OrganizationActivity.activity_id == activity.id)
            orgs_result = await db.execute(query)
            orgs = orgs_result.scalars().all()
            organizations.update(org.organization for org in orgs)

        return {"organizations": [org.name for org in organizations]}
    except Exception as e:
        return handle_exception(e)


@app.get("/organizations/search_by_name/",
         description="Ищет организации, имена которых содержат указанную строку")
async def search_organizations_by_name(name: str, db: AsyncSession = Depends(get_db)):
    try:
        query = select(Organization).where(Organization.name.ilike(f"%{name}%"))
        result = await db.execute(query)
        organizations = result.scalars().all()

        return {"organizations": [{
            "id": organization.id,
            "name": organization.name,
            "address": organization.building.address if organization.building else None,
            "phone_numbers": [pn.number for pn in organization.phone_numbers]
        } for organization in organizations]}
    except Exception as e:
        return handle_exception(e)


@app.post("/create_building/",
          description="Создает новую запись о здании по указанным адресом и координатами")
async def create_building(address: str, latitude: float, longitude: float, db: AsyncSession = Depends(get_db)):
    try:
        new_building = Building(address=address, latitude=latitude, longitude=longitude)
        db.add(new_building)
        await db.commit()
        await db.refresh(new_building)
        return {"id": new_building.id, "message": "Здание успешно создано"}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)
