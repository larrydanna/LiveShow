from __future__ import absolute_import

import json

from bottle import request, response, abort

from app import models, schemas
from app.database import SessionLocal


def _json(data, status=200):
    response.content_type = "application/json"
    response.status = status
    return json.dumps(data)


def _build_queue_detail(queue, db):
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
            script_items.append(schemas.queue_item_schema(item, script))
    return schemas.queue_detail(queue, script_items)


def setup_routes(app):

    @app.route("/api/queues", method="GET")
    def list_queues():
        db = SessionLocal()
        try:
            queues = db.query(models.ScriptQueue).all()
            return _json([schemas.queue_list_item(q) for q in queues])
        finally:
            db.close()

    @app.route("/api/queues/<queue_id:int>", method="GET")
    def get_queue(queue_id):
        db = SessionLocal()
        try:
            queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
            if not queue:
                abort(404, "Queue not found")
            return _json(_build_queue_detail(queue, db))
        finally:
            db.close()

    @app.route("/api/queues", method="POST")
    def create_queue():
        payload = request.json
        if not payload:
            abort(400, "Missing JSON body")
        db = SessionLocal()
        try:
            queue = models.ScriptQueue(name=payload.get("name", ""))
            db.add(queue)
            db.commit()
            db.refresh(queue)
            return _json(schemas.queue_list_item(queue), status=201)
        finally:
            db.close()

    @app.route("/api/queues/<queue_id:int>", method="PUT")
    def update_queue(queue_id):
        db = SessionLocal()
        try:
            queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
            if not queue:
                abort(404, "Queue not found")
            payload = request.json or {}
            if "name" in payload:
                queue.name = payload["name"]
            db.commit()
            db.refresh(queue)
            return _json(schemas.queue_list_item(queue))
        finally:
            db.close()

    @app.route("/api/queues/<queue_id:int>", method="DELETE")
    def delete_queue(queue_id):
        db = SessionLocal()
        try:
            queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
            if not queue:
                abort(404, "Queue not found")
            db.query(models.ScriptQueueItem).filter(
                models.ScriptQueueItem.queue_id == queue_id
            ).delete()
            db.delete(queue)
            db.commit()
            return _json({"ok": True})
        finally:
            db.close()

    @app.route("/api/queues/<queue_id:int>/scripts", method="POST")
    def add_script_to_queue(queue_id):
        payload = request.json or {}
        script_id = payload.get("script_id")
        if script_id is None:
            abort(400, "Missing script_id")
        db = SessionLocal()
        try:
            queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
            if not queue:
                abort(404, "Queue not found")
            script = db.query(models.Script).filter(models.Script.id == script_id).first()
            if not script:
                abort(404, "Script not found")
            position = payload.get("position", 0) or 0
            item = models.ScriptQueueItem(
                queue_id=queue_id,
                script_id=script_id,
                position=position,
            )
            db.add(item)
            db.commit()
            return _json(_build_queue_detail(queue, db))
        finally:
            db.close()

    @app.route("/api/queues/<queue_id:int>/scripts/<script_id:int>", method="DELETE")
    def remove_script_from_queue(queue_id, script_id):
        db = SessionLocal()
        try:
            queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
            if not queue:
                abort(404, "Queue not found")
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
            return _json(_build_queue_detail(queue, db))
        finally:
            db.close()

    @app.route("/api/queues/<queue_id:int>/scripts/reorder", method="PUT")
    def reorder_scripts(queue_id):
        db = SessionLocal()
        try:
            queue = db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
            if not queue:
                abort(404, "Queue not found")
            payload = request.json or []
            for reorder in payload:
                s_id = reorder.get("script_id")
                if s_id is None:
                    continue
                item = (
                    db.query(models.ScriptQueueItem)
                    .filter(
                        models.ScriptQueueItem.queue_id == queue_id,
                        models.ScriptQueueItem.script_id == s_id,
                    )
                    .first()
                )
                if item:
                    item.position = reorder.get("position", item.position)
            db.commit()
            return _json(_build_queue_detail(queue, db))
        finally:
            db.close()
