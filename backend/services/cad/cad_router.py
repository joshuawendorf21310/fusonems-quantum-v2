from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from utils.logger import logger

router = APIRouter(prefix="/api/cad", tags=["CAD"])

@router.get("/units")
def get_units():
    return {"active_units": [
        {"unit_id": "A1", "status": "Available", "location": [44.9, -89.6]},
        {"unit_id": "M2", "status": "En Route", "location": [44.95, -89.63]},
    ]}

@router.post("/dispatch")
def dispatch_unit(data: dict):
    logger.info(f"🚑 Dispatching {data.get('unit_id')} to call {data.get('call_id')}")
    return {"status": "dispatched", "data": data}
