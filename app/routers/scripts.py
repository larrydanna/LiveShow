from __future__ import absolute_import

import json

from bottle import request, response, abort

from app import models, schemas
from app.database import SessionLocal


def _json(data, status=200):
    response.content_type = "application/json"
    response.status = status
    return json.dumps(data)


def setup_routes(app):

    @app.route("/api/scripts", method="GET")
    def list_scripts():
        db = SessionLocal()
        try:
            items = db.query(models.Script).all()
            return _json([schemas.script_list_item(s) for s in items])
        finally:
            db.close()

    @app.route("/api/scripts/<script_id:int>", method="GET")
    def get_script(script_id):
        db = SessionLocal()
        try:
            script = db.query(models.Script).filter(models.Script.id == script_id).first()
            if not script:
                abort(404, "Script not found")
            return _json(schemas.script_detail(script))
        finally:
            db.close()

    @app.route("/api/scripts", method="POST")
    def create_script():
        payload = request.json
        if not payload:
            abort(400, "Missing JSON body")
        db = SessionLocal()
        try:
            script = models.Script(
                title=payload.get("title", ""),
                body=payload.get("body", ""),
                submitted_by=payload.get("submitted_by", ""),
            )
            db.add(script)
            db.commit()
            db.refresh(script)
            return _json(schemas.script_detail(script), status=201)
        finally:
            db.close()

    @app.route("/api/scripts/<script_id:int>", method="PUT")
    def update_script(script_id):
        db = SessionLocal()
        try:
            script = db.query(models.Script).filter(models.Script.id == script_id).first()
            if not script:
                abort(404, "Script not found")
            payload = request.json or {}
            for field in ("title", "body", "submitted_by"):
                if field in payload:
                    setattr(script, field, payload[field])
            db.commit()
            db.refresh(script)
            return _json(schemas.script_detail(script))
        finally:
            db.close()

    @app.route("/api/scripts/<script_id:int>", method="DELETE")
    def delete_script(script_id):
        db = SessionLocal()
        try:
            script = db.query(models.Script).filter(models.Script.id == script_id).first()
            if not script:
                abort(404, "Script not found")
            db.delete(script)
            db.commit()
            return _json({"ok": True})
        finally:
            db.close()
