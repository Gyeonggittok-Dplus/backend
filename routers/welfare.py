from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, HTTPException, Query

from schemas import WelfareAnnouncement, WelfareFacility

router = APIRouter()


def _get_conn():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not set")
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)


@router.get("/list")
def list_welfare_services(
        sigun_name: Optional[str] = Query(None, description="Optional Si/Gun filter"),
) -> List[Dict[str, Any]]:
    sql = """                                                                                                                                                     
        SELECT                                                                                                                                                    
            sigun_name,
            service_name,
            target,
            support_cycle,
            department,
            apply_method,
            service_url
        FROM tbwelfaressrsm
    """
    params: Dict[str, Any] = {}
    if sigun_name:
        sql += " WHERE sigun_name = %(sigun_name)s"
        params["sigun_name"] = sigun_name

    try:
        with _get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


    return rows


@router.get("/facilities", response_model=List[WelfareFacility])
def list_welfare_facilities(
        region: Optional[str] = Query(None, description="Optional city/county filter"),
) -> List[WelfareFacility]:
    sql = """                                                                                                                                                     
        SELECT                                                                                                                                                    
            facility_id,                                                                                                                                          
            name,                                                                                                                                                 
            category,                                                                                                                                             
            address,                                                                                                                                              
            region,                                                                                                                                               
            latitude,                                                                                                                                             
            longitude,                                                                                                                                            
            phone,                                                                                                                                                
            updated_at                                                                                                                                            
        FROM welfare_facilities                                                                                                                                   
    """
    params: Dict[str, Any] = {}
    if region:
        sql += " WHERE region = %(region)s"
        params["region"] = region

    try:
        with _get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return [WelfareFacility(**row) for row in rows]


@router.get("/announcements", response_model=List[WelfareAnnouncement])
def list_welfare_announcements(
        region: Optional[str] = Query(None, description="Optional city/county filter"),
) -> List[WelfareAnnouncement]:
    sql = """                                                                                                                                                     
        SELECT                                                                                                                                                    
            announcement_id,                                                                                                                                      
            title,                                                                                                                                                
            summary,                                                                                                                                              
            category,                                                                                                                                             
            apply_start_date,                                                                                                                                     
            apply_end_date,                                                                                                                                       
            region,                                                                                                                                               
            source_url                                                                                                                                            
        FROM welfare_announcements                                                                                                                                
    """
    params: Dict[str, Any] = {}
    if region:
        sql += " WHERE region = %(region)s"
        params["region"] = region

    try:
        with _get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return [WelfareAnnouncement(**row) for row in rows]
