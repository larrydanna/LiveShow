from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.get("", response_model=list[schemas.ScriptListItem])
def list_scripts(db: Session = Depends(get_db)):
    return db.query(models.Script).all()


@router.get("/{script_id}", response_model=schemas.ScriptDetail)
def get_script(script_id: int, db: Session = Depends(get_db)):
    script = db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.post("", response_model=schemas.ScriptDetail, status_code=201)
def create_script(payload: schemas.ScriptCreate, db: Session = Depends(get_db)):
    script = models.Script(**payload.model_dump())
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.put("/{script_id}", response_model=schemas.ScriptDetail)
def update_script(script_id: int, payload: schemas.ScriptUpdate, db: Session = Depends(get_db)):
    script = db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(script, field, value)
    db.commit()
    db.refresh(script)
    return script


@router.delete("/{script_id}")
def delete_script(script_id: int, db: Session = Depends(get_db)):
    script = db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    db.delete(script)
    db.commit()
    return {"ok": True}
