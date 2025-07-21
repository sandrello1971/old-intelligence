from pydantic import BaseModel

class HashtagSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
