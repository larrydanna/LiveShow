from __future__ import absolute_import

from flask import Blueprint, request, jsonify, g, abort
from app import models, schemas

blueprint = Blueprint("queues", __name__)


def _build_queue_detail(queue):
    items = (
        g.db.query(models.ScriptQueueItem)
        .filter(models.ScriptQueueItem.queue_id == queue.id)
        .order_by(models.ScriptQueueItem.position.asc())
        .all()
    )
    script_items = []
    for item in items:
        script = g.db.query(models.Script).filter(models.Script.id == item.script_id).first()
        if script:
            script_items.append(schemas.queue_item_schema(item, script))
    return schemas.queue_detail(queue, script_items)


@blueprint.route("/api/queues", methods=["GET"])
def list_queues():
    queues = g.db.query(models.ScriptQueue).all()
    return jsonify([schemas.queue_list_item(q) for q in queues])


@blueprint.route("/api/queues/<int:queue_id>", methods=["GET"])
def get_queue(queue_id):
    queue = g.db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        abort(404)
    return jsonify(_build_queue_detail(queue))


@blueprint.route("/api/queues", methods=["POST"])
def create_queue():
    payload = request.get_json()
    if not payload:
        abort(400)
    queue = models.ScriptQueue(name=payload.get("name", ""))
    g.db.add(queue)
    g.db.commit()
    g.db.refresh(queue)
    return jsonify(schemas.queue_list_item(queue)), 201


@blueprint.route("/api/queues/<int:queue_id>", methods=["PUT"])
def update_queue(queue_id):
    queue = g.db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        abort(404)
    payload = request.get_json() or {}
    if "name" in payload:
        queue.name = payload["name"]
    g.db.commit()
    g.db.refresh(queue)
    return jsonify(schemas.queue_list_item(queue))


@blueprint.route("/api/queues/<int:queue_id>", methods=["DELETE"])
def delete_queue(queue_id):
    queue = g.db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        abort(404)
    g.db.query(models.ScriptQueueItem).filter(models.ScriptQueueItem.queue_id == queue_id).delete()
    g.db.delete(queue)
    g.db.commit()
    return jsonify({"ok": True})


@blueprint.route("/api/queues/<int:queue_id>/scripts", methods=["POST"])
def add_script_to_queue(queue_id):
    queue = g.db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        abort(404)
    payload = request.get_json() or {}
    script_id = payload.get("script_id")
    if script_id is None:
        abort(400)
    script = g.db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        abort(404)
    position = payload.get("position", 0) or 0
    item = models.ScriptQueueItem(
        queue_id=queue_id,
        script_id=script_id,
        position=position,
    )
    g.db.add(item)
    g.db.commit()
    return jsonify(_build_queue_detail(queue))


@blueprint.route("/api/queues/<int:queue_id>/scripts/<int:script_id>", methods=["DELETE"])
def remove_script_from_queue(queue_id, script_id):
    queue = g.db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        abort(404)
    item = (
        g.db.query(models.ScriptQueueItem)
        .filter(
            models.ScriptQueueItem.queue_id == queue_id,
            models.ScriptQueueItem.script_id == script_id,
        )
        .first()
    )
    if item:
        g.db.delete(item)
        g.db.commit()
    return jsonify(_build_queue_detail(queue))


@blueprint.route("/api/queues/<int:queue_id>/scripts/reorder", methods=["PUT"])
def reorder_scripts(queue_id):
    queue = g.db.query(models.ScriptQueue).filter(models.ScriptQueue.id == queue_id).first()
    if not queue:
        abort(404)
    payload = request.get_json() or []
    for reorder in payload:
        s_id = reorder.get("script_id")
        if s_id is None:
            continue
        item = (
            g.db.query(models.ScriptQueueItem)
            .filter(
                models.ScriptQueueItem.queue_id == queue_id,
                models.ScriptQueueItem.script_id == s_id,
            )
            .first()
        )
        if item:
            item.position = reorder.get("position", item.position)
    g.db.commit()
    return jsonify(_build_queue_detail(queue))
