from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/queues", tags=["queues"])


def _build_queue_detail(queue: models.ScriptQueue, db: Session) -> schemas.QueueDetail:
    items = (
        db.query(models.ScriptQueueItem)
        .filter(models.ScriptQueueItem.queue_id == queue.id)
        .order_by(models.ScriptQueueItem.position.asc())
        .all()
    )
    script_items = []
    for item in items:
        script = db.query(models.Script).filter(models.Script.id == item.script_id).first()
        if script:
            script_items.append(
                schemas.QueueItemSchema(
                    id=item.id,
                    script_id=item.script_id,
                    position=item.position,
                    script=schemas.ScriptListItem.model_validate(script),
                )
            )
    return schemas.QueueDetail(
        id=queue.id,
        name=queue.name,
        created_at=queue.created_at,
        scripts=script_items,
    )


@router.get("/", response_model=list[schemas.QueueListItem])
def list_queues(db: Session = Depends(get_db)):
    return db.query(models.ScriptQueue).all()


@router.get("/{queue_id}", response_model=schemas.QueueDetail)
def get_queue(queue_id: int, db: Session = Depends(get_db)):
    queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    return _build_queue_detail(queue, db)


@router.post("/", response_model=schemas.QueueListItem, status_code=201)
def create_queue(payload: schemas.QueueCreate, db: Session = Depends(get_db)):
    queue = models.ScriptQueue(**payload.model_dump())
    db.add(queue)
    db.commit()
    db.refresh(queue)
    return queue


@router.put("/{queue_id}", response_model=schemas.QueueListItem)
def update_queue(queue_id: int, payload: schemas.QueueUpdate, db: Session = Depends(get_db)):
    queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(queue, field, value)
    db.commit()
    db.refresh(queue)
    return queue


@router.delete("/{queue_id}")
def delete_queue(queue_id: int, db: Session = Depends(get_db)):
    queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    db.query(models.ScriptQueueItem).filter(models.ScriptQueueItem.queue_id == queue_id).delete()
    db.delete(queue)
    db.commit()
    return {"ok": True}


@router.post("/{queue_id}/scripts", response_model=schemas.QueueDetail)
def add_script_to_queue(
    queue_id: int, payload: schemas.AddScriptToQueue, db: Session = Depends(get_db)
):
    queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    script = db.query(models.Script).filter(models.Script.id == payload.script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    item = models.ScriptQueueItem(
        queue_id=queue_id,
        script_id=payload.script_id,
        position=payload.position or 0,
    )
    db.add(item)
    db.commit()
    return _build_queue_detail(queue, db)


@router.delete("/{queue_id}/scripts/{script_id}", response_model=schemas.QueueDetail)
def remove_script_from_queue(queue_id: int, script_id: int, db: Session = Depends(get_db)):
    queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    item = (
        db.query(models.ScriptQueueItem)
        .filter(
            models.ScriptQueueItem.queue_id == queue_id,
            models.ScriptQueueItem.script_id == script_id,
        )
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
    return _build_queue_detail(queue, db)


@router.put("/{queue_id}/scripts/reorder", response_model=schemas.QueueDetail)
def reorder_scripts(
    queue_id: int, payload: list[schemas.ReorderItem], db: Session = Depends(get_db)
):
    queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    for reorder in payload:
        item = (
            db.query(models.ScriptQueueItem)
            .filter(
                models.ScriptQueueItem.queue_id == queue_id,
                models.ScriptQueueItem.script_id == reorder.script_id,
            )
            .first()
        )
        if item:
            item.position = reorder.position
    db.commit()
    return _build_queue_detail(queue, db)
