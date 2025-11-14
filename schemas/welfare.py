from __future__ import annotations

import hashlib
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


def _stable_id(*parts: Optional[str], prefix: str = "svc") -> Optional[str]:
    tokens = [p.strip() for p in parts if isinstance(p, str) and p and p.strip()]
    if not tokens:
        return None
    digest = hashlib.sha1("||".join(tokens).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"


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
        name = _pick(
            data,
            "SRVC_NM",
            "SERVC_NM",
            "SERVICE_NM",
            "PRGM_NM",
            "TITLE",
        )
        region = _pick(data, "SIGUN_NM", "BRSI_NM", "REGION_NM", "AREA_NM")
        application_url = _pick(data, "SERVC_RINK_ADDR", "SRVC_URL", "APPLY_URL", "RELATE_INFO", "LINK_URL", "HMPG_ADDR")
        service_id = (
            _pick(data, "SRVC_ID", "SERVC_ID", "SERVICE_ID", "ID", "REG_NO")
            or _stable_id(name, region, application_url, prefix="svc")
            or f"svc-{data.get('ROW_NUM', '0')}"
        )

        return cls(
            service_id=service_id,
            name=name or "TBD",
            summary=_pick(
                data,
                "SRVC_SUM",
                "SERVICE_SUM",
                "SUMMARY",
                "MAIN_PURPS",
                "SPORT_CYCL",
            ),
            benefit_detail=_pick(
                data,
                "SPRNT_CONT",
                "BENEFIT_CN",
                "BENEFIT_DETAIL",
                "SPORT_CN",
                "SPORT_TARGET",
                "GUID",
            ),
            eligibility=_pick(
                data,
                "TRGTER_RQISIT",
                "ELGBLTY_CN",
                "ELIGIBILITY",
                "SPORT_TARGET",
                "APLCATN_METH",
            ),
            region=region,
            managing_agency=_pick(
                data,
                "MANAGE_INST_NM",
                "CHRG_ORG_NM",
                "CHARGE_DEPT_NM",
                "OPERT_ORGNZT_NM",
                "OPERT_MAINBD_NM",
                "AGENCY_NM",
            ),
            contact=_pick(
                data,
                "MANAGE_INST_TELNO",
                "TELNO",
                "CONTACT",
                "GUID",
            ),
            application_url=application_url,
            updated_at=_pick(data, "UPDATE_DT", "REG_DT", "LAST_UPD_DT", "DATA_STD_DE"),
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
        facility_id = _pick(data, "FACLT_SN", "FACILITY_ID", "ID", "INST_ID") or _stable_id(
            _pick(data, "INST_NM", "FACLT_NM", "FACILITY_NM"),
            _pick(data, "SIGUN_NM", "REGION_NM"),
            _pick(data, "REFINE_ROADNM_ADDR", "REFINE_LOTNO_ADDR"),
            prefix="fac",
        )
        return cls(
            facility_id=facility_id or f"fac-{data.get('ROW_NUM', '0')}",
            name=_pick(data, "FACLT_NM", "FACILITY_NM", "CENTER_NM", "INST_NM") or "Unnamed facility",
            category=_pick(data, "FACLT_CL_NM", "CATEGORY_NM", "TYPE"),
            address=_pick(data, "REFINE_ROADNM_ADDR", "REFINE_LOTNO_ADDR", "ADDR"),
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
