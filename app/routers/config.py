import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/config", tags=["config"])

DEFAULT_INSTANCE_NAME = "LiveShow"
INSTANCE_NAME_KEY = "instance_name"
INSTANCE_NAME_MAX_LEN = 64

PEDAL_MAPPINGS_KEY = "pedal_mappings"
DEFAULT_PEDAL_MAPPINGS = [
    {"key": "a", "action": ""},
    {"key": "b", "action": "toggle_scroll"},
    {"key": "c", "action": ""},
]


@router.get("", response_model=schemas.InstanceConfigRead)
def get_config(db: Session = Depends(get_db)):
    row = db.query(models.AppConfig).filter(
        models.AppConfig.key == INSTANCE_NAME_KEY
    ).first()
    return {"instance_name": row.value if row else DEFAULT_INSTANCE_NAME}


@router.put("", response_model=schemas.InstanceConfigRead)
def update_config(payload: schemas.InstanceConfigUpdate, db: Session = Depends(get_db)):
    name = payload.instance_name.strip()[:INSTANCE_NAME_MAX_LEN]
    if not name:
        name = DEFAULT_INSTANCE_NAME
    row = db.query(models.AppConfig).filter(
        models.AppConfig.key == INSTANCE_NAME_KEY
    ).first()
    if row:
        row.value = name
    else:
        db.add(models.AppConfig(key=INSTANCE_NAME_KEY, value=name))
    db.commit()
    return {"instance_name": name}


@router.get("/pedal-mappings", response_model=schemas.PedalMappingsRead)
def get_pedal_mappings(db: Session = Depends(get_db)):
    row = db.query(models.AppConfig).filter(
        models.AppConfig.key == PEDAL_MAPPINGS_KEY
    ).first()
    if row:
        try:
            mappings = json.loads(row.value)
        except (json.JSONDecodeError, ValueError):
            mappings = DEFAULT_PEDAL_MAPPINGS
    else:
        mappings = DEFAULT_PEDAL_MAPPINGS
    return {"mappings": mappings}


@router.put("/pedal-mappings", response_model=schemas.PedalMappingsRead)
def update_pedal_mappings(
    payload: schemas.PedalMappingsUpdate,
    db: Session = Depends(get_db),
):
    mappings_data = [m.model_dump() for m in payload.mappings]
    mappings_json = json.dumps(mappings_data)
    row = db.query(models.AppConfig).filter(
        models.AppConfig.key == PEDAL_MAPPINGS_KEY
    ).first()
    if row:
        row.value = mappings_json
    else:
        db.add(models.AppConfig(key=PEDAL_MAPPINGS_KEY, value=mappings_json))
    db.commit()
    return {"mappings": mappings_data}
