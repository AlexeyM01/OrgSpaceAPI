"""
src/api/buildings.py
"""

from typing import Dict, Any

from fastapi import Depends, HTTPException, APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Building
from src.schemas import BuildingCreate
from src.utils import verify_api_key, handle_exception

router = APIRouter(
    prefix="/buildings",
    tags=["buildings"]
)


@router.post("/create/", dependencies=[Depends(verify_api_key)], response_model=None,
             description="Создает новую запись о здании по указанным адресом и координатами",
             status_code=status.HTTP_201_CREATED)
async def create_building(building: BuildingCreate,
                          db: AsyncSession = Depends(get_db)) -> Dict[str, Any] | JSONResponse:
    try:
        existing_building = await db.execute(
            select(Building).where(Building.address == building.address)
        )
        if existing_building.scalars().first() is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Здание уже существует")

        new_building = Building(**building.model_dump())
        db.add(new_building)
        await db.commit()
        await db.refresh(new_building)
        return {"id": new_building.id, "message": "Здание успешно создано"}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)


@router.put("/put/{building_id}/",
            description="Обновляет существующее здание",
            response_model=None)
async def update_building(building_id: int, building: BuildingCreate,
                          db: AsyncSession = Depends(get_db)) -> Dict[str, Any] | JSONResponse:
    try:
        existing_building_query = select(Building).where(Building.id == building_id)
        existing_building_result = await db.execute(existing_building_query)
        existing_building = existing_building_result.scalars().first()

        if not existing_building:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Здание не найдено")

        existing_building.address = building.address
        existing_building.latitude = building.latitude
        existing_building.longitude = building.longitude

        await db.commit()
        await db.refresh(existing_building)
        return {"id": existing_building.id, "address": existing_building.address}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)


@router.delete("/delete/{building_id}/",
               description="Удаляет здание")
async def delete_building(building_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str] | JSONResponse:
    try:
        building_query = select(Building).where(Building.id == building_id)
        building_result = await db.execute(building_query)
        building = building_result.scalars().first()
        if not building:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Здание не найдено")

        await db.delete(building)
        await db.commit()
        return {"message": f"Здание с ID {building_id} успешно удалено"}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)
