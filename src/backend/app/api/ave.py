from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import httpx

from .auth import get_current_user
from ..core.database import get_db
from ..core.config import get_settings
from ..db.models import User
from ..services.ave import AveCloudClient, check_tier_access
from ..db.schemas import (
    AveBatchPricesRequest,
    AveKlinesRequest,
    AveChainQuoteRequest,
    AveChainSwapRequest,
)

router = APIRouter()


def get_ave_client() -> AveCloudClient:
    settings = get_settings()
    return AveCloudClient(api_key=settings.AVE_API_KEY, plan=settings.AVE_API_PLAN)


@router.get("/tokens")
async def search_tokens(
    query: Optional[str] = None,
    chain: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    client = get_ave_client()
    try:
        tokens = await client.get_tokens(query=query, chain=chain, limit=limit)
        return {"tokens": tokens}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AVE API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tokens: {str(e)}",
        )


@router.post("/tokens/price")
async def get_batch_prices(
    request: AveBatchPricesRequest,
    current_user: User = Depends(get_current_user),
):
    client = get_ave_client()
    try:
        prices = await client.get_batch_prices(request.token_ids)
        return {"prices": prices}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AVE API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch batch prices: {str(e)}",
        )


@router.get("/tokens/{token_id}")
async def get_token_details(
    token_id: str,
    current_user: User = Depends(get_current_user),
):
    client = get_ave_client()
    try:
        token = await client.get_token_details(token_id)
        if token is None:
            return {"token": None, "upsell_message": None}
        return {"token": token}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AVE API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch token details: {str(e)}",
        )


@router.get("/klines/{token_id}")
async def get_klines(
    token_id: str,
    interval: str = "1h",
    limit: int = 100,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    client = get_ave_client()
    try:
        klines = await client.get_klines(
            token_id=token_id,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time,
        )
        return {"klines": klines}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AVE API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch klines: {str(e)}",
        )


@router.get("/tokens/trending")
async def get_trending_tokens(
    chain: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    client = get_ave_client()
    try:
        tokens = await client.get_trending_tokens(chain=chain, limit=limit)
        return {"tokens": tokens}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AVE API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trending tokens: {str(e)}",
        )


@router.get("/contracts/{contract_id}")
async def get_token_risk(
    contract_id: str,
    current_user: User = Depends(get_current_user),
):
    client = get_ave_client()
    try:
        risk = await client.get_token_risk(contract_id)
        if risk is None:
            return {"risk": None, "upsell_message": None}
        return {"risk": risk}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AVE API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch token risk: {str(e)}",
        )


@router.post("/chain/quote")
async def get_chain_quote(
    request: AveChainQuoteRequest,
    current_user: User = Depends(get_current_user),
):
    client = get_ave_client()
    try:
        quote = await client.get_chain_quote(
            chain=request.chain,
            from_token=request.from_token,
            to_token=request.to_token,
            amount=request.amount,
            slippage=request.slippage,
        )
        if quote is None:
            return {"quote": None, "upsell_message": None}
        return {"quote": quote}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AVE API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chain quote: {str(e)}",
        )


@router.post("/chain/swap")
async def get_chain_swap(
    request: AveChainSwapRequest,
    current_user: User = Depends(get_current_user),
):
    client = get_ave_client()
    try:
        swap = await client.get_chain_swap(
            chain=request.chain,
            from_token=request.from_token,
            to_token=request.to_token,
            amount=request.amount,
            slippage=request.slippage,
            wallet_address=request.wallet_address,
        )
        if swap is None:
            return {"swap": None, "upsell_message": None}
        return {"swap": swap}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"AVE API error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chain swap: {str(e)}",
        )
