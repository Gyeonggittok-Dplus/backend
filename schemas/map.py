from pydantic import BaseModel
from typing import List, Optional
class Facility(BaseModel):
    name: str
    phone: Optional[str]
    lot_addr: Optional[str]
    road_addr: Optional[str]
    lo_addr: str
    lat: float
    lng: float

class FacilityResponse(BaseModel):
    code: int
    message: str
    data: List[Facility]
    user_location: str