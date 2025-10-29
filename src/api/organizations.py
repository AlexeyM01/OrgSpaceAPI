from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from src.database import get_db
from src.models import Building, Organization, Activity, OrganizationActivity, PhoneNumber
from src.schemas import OrganizationCreate, OrganizationUpdate
from src.utils import verify_api_key, handle_exception

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"]
)


@router.get("/by_building_address/", dependencies=[Depends(verify_api_key)],
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


@router.get("/organizations/by_activity_name/", dependencies=[Depends(verify_api_key)],
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

        if not organizations:
            return JSONResponse(status_code=404, content={"message": "Организаций не найдено"})

        return {"organizations": [org.organization.name for org in organizations]}
    except Exception as e:
        return handle_exception(e)


@router.get("/by_area/", dependencies=[Depends(verify_api_key)],
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

        if not buildings:
            return JSONResponse(status_code=404, content={"message": "Зданий не найдено"})
        return {"buildings": [{"id": b.id, "address": b.address} for b in buildings]}
    except Exception as e:
        return handle_exception(e)


@router.get("/{org_id}/", dependencies=[Depends(verify_api_key)],
            description="Получает детали организации по ID")
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


@router.get("/search_by_activity/", dependencies=[Depends(verify_api_key)])
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

        if not organizations:
            return JSONResponse(status_code=404, content={"message": "Организаций не найдено"})
        return {"organizations": [org.name for org in organizations]}
    except Exception as e:
        return handle_exception(e)


@router.get("/search_by_name/", dependencies=[Depends(verify_api_key)],
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


@router.post("/create/", dependencies=[Depends(verify_api_key)], response_model=None,
             description="Создает новую организацию по указанным данным", status_code=status.HTTP_201_CREATED)
async def create_organization(organization: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    try:
        existing_organization_query = select(Organization).where(Organization.name == organization.name)
        existing_organization_result = await db.execute(existing_organization_query)
        existing_organization = existing_organization_result.scalars().first()
        if existing_organization:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Организация с таким именем уже существует")

        building_query = select(Building).where(Building.id == organization.building_id)
        building_result = await db.execute(building_query)
        building = building_result.scalars().first()
        if not building:
            return JSONResponse(status_code=404, content={"message": "Здание не найдено"})

        new_organization = Organization(name=organization.name, building_id=organization.building_id)
        db.add(new_organization)
        await db.commit()
        await db.refresh(new_organization)

        for phone in organization.phone_numbers:
            phone_number = PhoneNumber(number=phone.number, organization_id=new_organization.id)
            db.add(phone_number)

        for activity_id in organization.activity_ids:
            activity_query = select(Activity).where(Activity.id == activity_id)
            activity_result = await db.execute(activity_query)
            activity = activity_result.scalars().first()
            if activity:
                org_activity = OrganizationActivity(organization_id=new_organization.id, activity_id=activity.id)
                db.add(org_activity)

        await db.commit()
        return {"id": new_organization.id, "name": new_organization.name}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)


@router.put("/{org_id}/",
            description="Обновляет существующую организацию",
            response_model=None)
async def update_organization(org_id: int, organization: OrganizationUpdate, db: AsyncSession = Depends(get_db)):
    try:
        existing_organization_query = select(Organization).where(Organization.id == org_id)
        existing_organization_result = await db.execute(existing_organization_query)
        existing_organization = existing_organization_result.scalars().first()

        if not existing_organization:
            raise HTTPException(status_code=404, detail="Организация не найдена")

        if organization.name is not None:
            existing_organization.name = organization.name
        if organization.building_id is not None:
            building_query = select(Building).where(Building.id == organization.building_id)
            building_result = await db.execute(building_query)
            building = building_result.scalars().first()
            if not building:
                raise HTTPException(status_code=400, detail="Здание не найдено")
            existing_organization.building_id = organization.building_id

        if organization.phone_numbers is not None:
            existing_phone_numbers = await db.execute(select(PhoneNumber).where(PhoneNumber.organization_id == org_id))
            for phone_number in existing_phone_numbers.scalars().all():
                await db.delete(phone_number)

            for phone in organization.phone_numbers:
                phone_number = PhoneNumber(number=phone.number, organization_id=existing_organization.id)
                db.add(phone_number)

        if organization.activity_ids is not None:
            activity_query = select(OrganizationActivity).where(OrganizationActivity.organization_id == org_id)
            activity_result = await db.execute(activity_query)
            existing_activities = activity_result.scalars().all()
            for activity in existing_activities:
                await db.delete(activity)

            for activity_id in organization.activity_ids:
                activity_query = select(Activity).where(Activity.id == activity_id)
                activity_result = await db.execute(activity_query)
                activity = activity_result.scalars().first()
                if activity:
                    org_activity = OrganizationActivity(organization_id=existing_organization.id,
                                                        activity_id=activity.id)
                    db.add(org_activity)

        await db.commit()
        await db.refresh(existing_organization)
        return {"id": existing_organization.id, "name": existing_organization.name}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)


@router.delete("/delete/{org_id}/",
               description="Удаляет организацию")
async def delete_organization(org_id: int, db: AsyncSession = Depends(get_db)):
    try:
        organization_query = select(Organization).where(Organization.id == org_id)
        organization_result = await db.execute(organization_query)
        organization = organization_result.scalars().first()
        if not organization:
            raise HTTPException(status_code=404, detail="Организация не найдена")

        await db.delete(organization)
        await db.commit()
        return {"message": f"Организация с ID {org_id} успешно удалена"}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)
