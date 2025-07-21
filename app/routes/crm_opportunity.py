from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import requests
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

CRM_BASE_URL = "https://app.crmincloud.it/api/v1"
CRM_USERNAME = os.getenv("CRM_USERNAME")
CRM_PASSWORD = os.getenv("CRM_PASSWORD")
CRM_API_KEY = os.getenv("CRM_API_KEY")

class OpportunityRequest(BaseModel):
    title: str
    cross_id: int = Field(..., alias="crossId")
    owner_id: int = Field(..., alias="ownerId")
    description: str
    phase_id: int = Field(53002, alias="phase")
    category_id: int = Field(25309, alias="category")
    status: int
    sales_persons: list[int] = Field(..., alias="salesPersons")
    budget: float
    amount: float

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True

def get_crm_token():
    url = f"{CRM_BASE_URL}/Auth/Login"
    payload = {
        "grant_type": "password",
        "userName": CRM_USERNAME,
        "password": CRM_PASSWORD
    }
    headers = {
        "WebApiKey": CRM_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Errore durante l'autenticazione con il CRM.")
    return response.json()["access_token"]

@router.post("/crm/create-opportunity")
def create_opportunity(opportunity: OpportunityRequest):
    token = get_crm_token()
    url = f"{CRM_BASE_URL}/Opportunity/CreateOrUpdate"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = opportunity.dict(by_alias=True)
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Errore durante la creazione dell'opportunità: {response.text}")
    return {"opportunity_id": response.json()}
