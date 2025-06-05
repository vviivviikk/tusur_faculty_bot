from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.user import User
from bot.utils.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
async def create_user(user_data: dict, db: AsyncSession = Depends(get_db)):
    new_user = User(**user_data)
    db.add(new_user)
    await db.commit()
    return {"id": new_user.id}

@router.get("/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
