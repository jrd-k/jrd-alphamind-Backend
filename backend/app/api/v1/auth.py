from fastapi import APIRouter, Depends

router = APIRouter()


@router.post("/login")
async def login():
    return {"message": "login placeholder"}


@router.post("/register")
async def register():
    return {"message": "register placeholder"}
