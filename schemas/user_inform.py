from pydantic import BaseModel

class UserInformBody(BaseModel):
    email: str
    age: int
    location: str
    sex: str
class GoogleVerifyBody(BaseModel):
    id_token: str