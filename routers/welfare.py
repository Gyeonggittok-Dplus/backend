from __future__ import annotations

from functools import wraps
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from schemas import WelfareAnnouncement, WelfareFacility, WelfareService
from services.gyeonggi_openapi import (
    GyeonggiOpenAPIClient,
    GyeonggiOpenAPIError,
    get_gyeonggi_client,
)

router = APIRouter()


def _map_errors(func):
    """Translate client-layer errors into HTTP responses."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GyeonggiOpenAPIError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return wrapper


@router.get("/list", response_model=List[WelfareService])
@_map_errors
def list_welfare_services(
    region: Optional[str] = Query(None, description="Optional city/county filter"),
    client: GyeonggiOpenAPIClient = Depends(get_gyeonggi_client),
) -> List[WelfareService]:
    services = client.fetch_welfare_services(region=region)
    return services


@router.get("/list/senior", response_model=List[WelfareService])
@_map_errors
def list_senior_services(
    client: GyeonggiOpenAPIClient = Depends(get_gyeonggi_client),
) -> List[WelfareService]:
    services = client.fetch_senior_services()
    return services


@router.get("/list/youth", response_model=List[WelfareService])
@_map_errors
def list_youth_services(
    client: GyeonggiOpenAPIClient = Depends(get_gyeonggi_client),
) -> List[WelfareService]:
    services = client.fetch_youth_services()
    return services


@router.get("/facilities", response_model=List[WelfareFacility])
@_map_errors
def list_welfare_facilities(
    region: Optional[str] = Query(None, description="Optional city/county filter"),
    client: GyeonggiOpenAPIClient = Depends(get_gyeonggi_client),
) -> List[WelfareFacility]:
    facilities = client.fetch_facilities(region=region)
    return facilities


@router.get("/announcements", response_model=List[WelfareAnnouncement])
@_map_errors
def list_welfare_announcements(
    region: Optional[str] = Query(None, description="Optional city/county filter"),
    client: GyeonggiOpenAPIClient = Depends(get_gyeonggi_client),
) -> List[WelfareAnnouncement]:
    announcements = client.fetch_announcements(region=region)
    return announcements
