"""
src/api/activities.py
"""

from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Activity
from fastapi import APIRouter

from src.utils import verify_api_key, handle_exception

router = APIRouter(
    prefix="/activities",
    tags=["activities"]
)


@router.post("/", dependencies=[Depends(verify_api_key)],
             summary="Создать новую активность",
             description="Создает новую активность, возможно, под родительской активностью",
             status_code=status.HTTP_201_CREATED)
async def create_activity(name: str, parent_id: int = None,
                          db: AsyncSession = Depends(get_db)) -> Dict[str, Any] | JSONResponse:
    try:
        if parent_id is not None:
            parent_activity_query = select(Activity).where(Activity.id == parent_id)
            parent_activity_result = await db.execute(parent_activity_query)
            parent_activity = parent_activity_result.scalars().first()

            if not parent_activity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Под такой ID нет родительской активности")
            if parent_activity.level is not None and parent_activity.level >= 3:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Нельзя создать активность глубиной больше трёх")

        new_activity = Activity(name=name, parent_id=parent_id)
        db.add(new_activity)
        await db.commit()
        await db.refresh(new_activity)
        return {"id": new_activity.id, "name": new_activity.name}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)


@router.delete("/{activity_id}/",
               description="Удаляет активность",
               status_code=status.HTTP_200_OK)
async def delete_activity(activity_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, str] | JSONResponse:
    try:
        activity_query = select(Activity).where(Activity.id == activity_id)
        activity_result = await db.execute(activity_query)
        activity = activity_result.scalars().first()
        if not activity:
            raise HTTPException(status_code=404, detail="Активность не найдена")

        await db.delete(activity)
        await db.commit()
        return {"message": f"Активность с ID {activity_id} успешно удалена"}
    except Exception as e:
        await db.rollback()
        return handle_exception(e)
