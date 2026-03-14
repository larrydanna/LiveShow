from __future__ import absolute_import

from flask import Blueprint, request, jsonify, g, abort
from app import models, schemas

blueprint = Blueprint("scripts", __name__)


@blueprint.route("/api/scripts", methods=["GET"])
def list_scripts():
    items = g.db.query(models.Script).all()
    return jsonify([schemas.script_list_item(s) for s in items])


@blueprint.route("/api/scripts/<int:script_id>", methods=["GET"])
def get_script(script_id):
    script = g.db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        abort(404)
    return jsonify(schemas.script_detail(script))


@blueprint.route("/api/scripts", methods=["POST"])
def create_script():
    payload = request.get_json()
    if not payload:
        abort(400)
    script = models.Script(
        title=payload.get("title", ""),
        body=payload.get("body", ""),
        submitted_by=payload.get("submitted_by", ""),
    )
    g.db.add(script)
    g.db.commit()
    g.db.refresh(script)
    return jsonify(schemas.script_detail(script)), 201


@blueprint.route("/api/scripts/<int:script_id>", methods=["PUT"])
def update_script(script_id):
    script = g.db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        abort(404)
    payload = request.get_json() or {}
    for field in ("title", "body", "submitted_by"):
        if field in payload:
            setattr(script, field, payload[field])
    g.db.commit()
    g.db.refresh(script)
    return jsonify(schemas.script_detail(script))


@blueprint.route("/api/scripts/<int:script_id>", methods=["DELETE"])
def delete_script(script_id):
    script = g.db.query(models.Script).filter(models.Script.id == script_id).first()
    if not script:
        abort(404)
    g.db.delete(script)
    g.db.commit()
    return jsonify({"ok": True})
