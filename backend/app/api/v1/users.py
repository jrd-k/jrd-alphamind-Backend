from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_users():
    return [{"id": 1, "username": "alice"}]


@router.get("/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id, "username": "user"}
