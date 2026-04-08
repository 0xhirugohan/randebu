from fastapi import APIRouter

router = APIRouter()


@router.get("/chains")
def get_chains():
    return {"chains": []}


@router.get("/tokens")
def get_tokens():
    return {"tokens": []}
