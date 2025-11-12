from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


def _pick(mapping: Dict[str, Any], *keys: str) -> Optional[str]:
    """Return the first non-empty string value for the provided keys."""
    for key in keys:
        value = mapping.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _as_float(value: Any) -> Optional[float]:
    if value in (None, "", " "):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


class WelfareService(BaseModel):
    service_id: str = Field(..., description="Unique service identifier from the open API")
    name: str = Field(..., description="Official service name")
    summary: Optional[str] = Field(None, description="Short human friendly description")
    benefit_detail: Optional[str] = Field(None, description="Detailed benefit description")
    eligibility: Optional[str] = Field(None, description="Eligibility criteria text")
    region: Optional[str] = Field(None, description="City/county name")
    managing_agency: Optional[str] = Field(None, description="Managing department or agency")
    contact: Optional[str] = Field(None, description="Phone or email contact")
    application_url: Optional[str] = Field(None, description="External application or detail URL")
    updated_at: Optional[str] = Field(None, description="Timestamp from the open API")

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "WelfareService":
        return cls(
            service_id=_pick(data, "SRVC_ID", "SERVICE_ID", "ID") or f"svc-{data.get('ROW_NUM', '0')}",
            name=_pick(data, "SRVC_NM", "SERVICE_NM", "TITLE") or "TBD",
            summary=_pick(data, "SRVC_SUM", "SERVICE_SUM", "SUMMARY"),
            benefit_detail=_pick(data, "SPRNT_CONT", "BENEFIT_CN", "BENEFIT_DETAIL"),
            eligibility=_pick(data, "TRGTER_RQISIT", "ELGBLTY_CN", "ELIGIBILITY"),
            region=_pick(data, "SIGUN_NM", "BRSI_NM", "REGION_NM"),
            managing_agency=_pick(data, "MANAGE_INST_NM", "CHRG_ORG_NM", "AGENCY_NM"),
            contact=_pick(data, "MANAGE_INST_TELNO", "TELNO", "CONTACT"),
            application_url=_pick(data, "SRVC_URL", "APPLY_URL", "LINK_URL"),
            updated_at=_pick(data, "UPDATE_DT", "REG_DT", "LAST_UPD_DT"),
        )


class WelfareFacility(BaseModel):
    facility_id: str = Field(..., description="Unique facility identifier")
    name: str
    category: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "WelfareFacility":
        return cls(
            facility_id=_pick(data, "FACLT_SN", "FACILITY_ID", "ID") or f"fac-{data.get('ROW_NUM', '0')}",
            name=_pick(data, "FACLT_NM", "FACILITY_NM", "CENTER_NM") or "Unnamed facility",
            category=_pick(data, "FACLT_CL_NM", "CATEGORY_NM", "TYPE"),
            address=_pick(data, "REFINE_LOTNO_ADDR", "REFINE_ROADNM_ADDR", "ADDR"),
            region=_pick(data, "SIGUN_NM", "CTPRVN_NM", "REGION_NM"),
            latitude=_as_float(_pick(data, "REFINE_WGS84_LAT", "LAT")),
            longitude=_as_float(_pick(data, "REFINE_WGS84_LOGT", "LNG")),
            phone=_pick(data, "TELNO", "MANAGE_INST_TELNO", "PHONE"),
            updated_at=_pick(data, "DATA_STD_DE", "UPDATE_DT", "LAST_UPD_DT"),
        )


class WelfareAnnouncement(BaseModel):
    announcement_id: str = Field(..., description="Unique announcement identifier")
    title: str
    summary: Optional[str] = None
    category: Optional[str] = None
    apply_start_date: Optional[str] = None
    apply_end_date: Optional[str] = None
    region: Optional[str] = None
    source_url: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "WelfareAnnouncement":
        return cls(
            announcement_id=_pick(data, "ANCM_ID", "NOTICE_ID", "ID") or f"anc-{data.get('ROW_NUM', '0')}",
            title=_pick(data, "ANCM_TITLE", "NOTICE_TITLE", "TITLE") or "Untitled announcement",
            summary=_pick(data, "ANCM_CN", "NOTICE_SUMMARY", "SUMMARY"),
            category=_pick(data, "ANCM_SE", "CATEGORY", "TYPE"),
            apply_start_date=_pick(data, "RCEPT_BGNDE", "APPLY_BEGIN", "START_DT"),
            apply_end_date=_pick(data, "RCEPT_ENDDE", "APPLY_END", "END_DT"),
            region=_pick(data, "SIGUN_NM", "REGION_NM", "AREA"),
            source_url=_pick(data, "ANCM_DETAIL_URL", "DETAIL_URL", "LINK_URL"),
        )
