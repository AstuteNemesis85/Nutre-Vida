from pydantic import BaseModel
from typing import Optional

class GoogleUserCreate(BaseModel):
    google_id: str
    email: str
    name: str
    picture: Optional[str] = None