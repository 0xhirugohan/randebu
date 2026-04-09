from fastapi import APIRouter

from ..core.config import get_settings
from ..services.ave import AveCloudClient

router = APIRouter()


@router.get("/chains")
def get_chains():
    return {"chains": ["bsc"]}


@router.get("/tokens")
async def get_tokens():
    settings = get_settings()
    client = AveCloudClient(api_key=settings.AVE_API_KEY, plan=settings.AVE_API_PLAN)
    tokens = await client.get_tokens(chain="bsc", limit=100)
    return {"tokens": tokens}
