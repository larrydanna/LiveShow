from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/config", tags=["config"])

DEFAULT_INSTANCE_NAME = "LiveShow"
INSTANCE_NAME_KEY = "instance_name"
INSTANCE_NAME_MAX_LEN = 64


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
