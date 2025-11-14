from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx

from schemas import WelfareAnnouncement, WelfareFacility, WelfareService

DEFAULT_BASE_URL = "https://openapi.gg.go.kr"
# 경기 복지 서비스 현황 (TBWELFARESSRSM) 데이터셋을 기본값으로 사용한다.
DEFAULT_SERVICE_DATASET = os.getenv("GYEONGGI_SERVICE_DATASET", "TBWELFARESSRSM")
DEFAULT_FACILITY_DATASET = os.getenv("GYEONGGI_FACILITY_DATASET", "GGD_HOUSING_WELFARE_INST")
DEFAULT_ANNOUNCEMENT_DATASET = os.getenv("GYEONGGI_ANNOUNCEMENT_DATASET", "GGD_WELFARE_NOTICE")


class GyeonggiOpenAPIError(RuntimeError):
    pass


class GyeonggiOpenAPIClient:
    """Utility wrapper around the Gyeonggi open API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = 20.0,
    ) -> None:
        self.api_key = api_key or os.getenv("GYEONGGI_OPENAPI_KEY")
        if not self.api_key:
            raise GyeonggiOpenAPIError("GYEONGGI_OPENAPI_KEY is not set")
        self.base_url = base_url or os.getenv("GYEONGGI_OPENAPI_BASE_URL", DEFAULT_BASE_URL)
        self.timeout = timeout
        self._client = httpx.Client(timeout=self.timeout)

    def _request(self, dataset: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        query = {
            "KEY": self.api_key,
            "Type": "json",
            "pIndex": params.pop("page", 1) if params else 1,
            "pSize": params.pop("page_size", 1000) if params else 1000,
        }
        if params:
            query.update(params)
        print(params)
        url = f"{self.base_url.rstrip('/')}/{dataset}"
        response = self._client.get(url, params=query)
        try:
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # pragma: no cover - network errors handled as runtime issues
            raise GyeonggiOpenAPIError(f"Failed to call {dataset}: {exc}") from exc

        rows = self._extract_rows(payload, dataset)
        return rows

    @staticmethod
    def _extract_rows(payload: Dict[str, Any], dataset: str) -> List[Dict[str, Any]]:
        """Handle variations of the open API response envelope."""
        for key in (dataset, dataset.upper(), dataset.lower()):
            if key in payload and isinstance(payload[key], list):
                for section in payload[key]:
                    if isinstance(section, dict) and "row" in section:
                        return section["row"]
        # fallback: search entire payload
        for value in payload.values():
            if isinstance(value, list):
                for section in value:
                    rows = section.get("row")
                    if rows:
                        return rows
        return []

    def fetch_welfare_services(self, region: Optional[str] = None) -> List[WelfareService]:
        params: Dict[str, Any] = {}
        if region:
            params["SIGUN_NM"] = region
        rows = self._request(DEFAULT_SERVICE_DATASET, params=params)
        return [WelfareService.from_api(row) for row in rows]

    def fetch_facilities(self, region: Optional[str] = None) -> List[WelfareFacility]:
        params: Dict[str, Any] = {}
        if region:
            params["SIGUN_NM"] = region
        rows = self._request(DEFAULT_FACILITY_DATASET, params=params)
        return [WelfareFacility.from_api(row) for row in rows]

    def fetch_announcements(self, region: Optional[str] = None) -> List[WelfareAnnouncement]:
        params: Dict[str, Any] = {}
        if region:
            params["SIGUN_NM"] = region
        rows = self._request(DEFAULT_ANNOUNCEMENT_DATASET, params=params)
        return [WelfareAnnouncement.from_api(row) for row in rows]


@lru_cache(maxsize=1)
def get_gyeonggi_client() -> GyeonggiOpenAPIClient:
    """FastAPI dependency helper."""
    return GyeonggiOpenAPIClient()
