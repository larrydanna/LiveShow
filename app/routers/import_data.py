"""POST /api/import – best-effort import from a LiveShow export JSON file."""

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app import match, models
from app.database import get_db

router = APIRouter(prefix="/api/import", tags=["import"])

# ── outcome constants ──────────────────────────────────────────────────────────
IMPORTED = "imported"
SKIPPED_NEAR_MATCH = "skipped_near_match"
SKIPPED_CONFLICT = "skipped_conflict_existing_queue"
SKIPPED_MISSING_DEP = "skipped_missing_dependency"
FAILED_VALIDATION = "failed_validation"
FAILED_PARSE = "failed_parse"


def _detail(
    obj_type: str,
    file_id: Any,
    outcome: str,
    message: str,
    *,
    created_id: Any = None,
    candidates: list | None = None,
) -> dict:
    d: dict[str, Any] = {
        "type": obj_type,
        "file_id": file_id,
        "outcome": outcome,
        "message": message,
    }
    if created_id is not None:
        d["created_id"] = created_id
    if candidates is not None:
        d["candidates"] = candidates
    return d


@router.post("")
async def import_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # ── 1. Parse upload ────────────────────────────────────────────────────────
    raw = await file.read()
    try:
        payload = json.loads(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON root must be an object.")

    details: list[dict] = []

    # ── 2. Import scripts ──────────────────────────────────────────────────────
    # file_id → new DB id (only populated for actually-imported scripts)
    script_id_map: dict[int, int] = {}

    existing_scripts = db.query(models.Script).all()

    for raw_script in payload.get("scripts", []):
        file_id = raw_script.get("id")
        try:
            title = str(raw_script.get("title") or "").strip()
            body = str(raw_script.get("body") or "").strip()
            submitted_by = str(raw_script.get("submitted_by") or "").strip()

            if not title or not body or not submitted_by:
                details.append(
                    _detail(
                        "script",
                        file_id,
                        FAILED_VALIDATION,
                        "Script missing required field(s): title, body, or submitted_by.",
                    )
                )
                continue

            candidates = match.find_near_match(title, body, existing_scripts)
            if candidates:
                details.append(
                    _detail(
                        "script",
                        file_id,
                        SKIPPED_NEAR_MATCH,
                        f"Script '{title}' is similar to {len(candidates)} existing script(s); skipped to avoid duplicates.",
                        candidates=candidates,
                    )
                )
                continue

            new_script = models.Script(
                title=title,
                body=body,
                submitted_by=submitted_by,
                font_face=str(raw_script.get("font_face") or "").strip() or None,
                font_size=str(raw_script.get("font_size") or "").strip() or None,
                created_at=datetime.now(timezone.utc),
            )
            sp = db.begin_nested()
            try:
                db.add(new_script)
                db.flush()  # get the new id
                sp.commit()
            except Exception as db_exc:
                sp.rollback()
                raise db_exc

            script_id_map[file_id] = new_script.id
            existing_scripts.append(new_script)  # include in future near-match checks

            details.append(
                _detail(
                    "script",
                    file_id,
                    IMPORTED,
                    f"Script '{title}' imported successfully.",
                    created_id=new_script.id,
                )
            )
        except Exception as exc:
            details.append(
                _detail(
                    "script",
                    file_id,
                    FAILED_PARSE,
                    f"Unexpected error: {exc}",
                )
            )

    # ── 3. Import queues + queue items ─────────────────────────────────────────
    existing_queue_names = {
        q.name for q in db.query(models.ScriptQueue.name).all()
    }

    for raw_queue in payload.get("queues", []):
        q_file_id = raw_queue.get("id")
        try:
            q_name = str(raw_queue.get("name") or "").strip()

            if not q_name:
                details.append(
                    _detail(
                        "queue",
                        q_file_id,
                        FAILED_VALIDATION,
                        "Queue missing required field: name.",
                    )
                )
                continue

            if q_name in existing_queue_names:
                details.append(
                    _detail(
                        "queue",
                        q_file_id,
                        SKIPPED_CONFLICT,
                        f"Queue '{q_name}' already exists; skipped (create-only policy).",
                    )
                )
                # queue items that depend on this queue are also skipped
                for raw_item in raw_queue.get("scripts", []):
                    details.append(
                        _detail(
                            "queue_item",
                            raw_item.get("id"),
                            SKIPPED_MISSING_DEP,
                            f"Queue item skipped because parent queue '{q_name}' was not created.",
                        )
                    )
                continue

            new_queue = models.ScriptQueue(
                name=q_name,
                created_at=datetime.now(timezone.utc),
            )
            sp = db.begin_nested()
            try:
                db.add(new_queue)
                db.flush()
                sp.commit()
            except Exception as db_exc:
                sp.rollback()
                raise db_exc
            existing_queue_names.add(q_name)

            details.append(
                _detail(
                    "queue",
                    q_file_id,
                    IMPORTED,
                    f"Queue '{q_name}' imported successfully.",
                    created_id=new_queue.id,
                )
            )

            # ── queue items ────────────────────────────────────────────────────
            for raw_item in raw_queue.get("scripts", []):
                item_file_id = raw_item.get("id")
                file_script_id = raw_item.get("script_id")
                position = raw_item.get("position", 0)

                new_script_id = script_id_map.get(file_script_id)
                if new_script_id is None:
                    details.append(
                        _detail(
                            "queue_item",
                            item_file_id,
                            SKIPPED_MISSING_DEP,
                            (
                                f"Queue item (file script_id={file_script_id}) skipped "
                                "because the referenced script was not imported "
                                "(it was skipped as a near-match, failed, or absent)."
                            ),
                        )
                    )
                    continue

                new_item = models.ScriptQueueItem(
                    queue_id=new_queue.id,
                    script_id=new_script_id,
                    position=position,
                )
                item_sp = db.begin_nested()
                try:
                    db.add(new_item)
                    db.flush()
                    item_sp.commit()
                except Exception as db_exc:
                    item_sp.rollback()
                    details.append(
                        _detail(
                            "queue_item",
                            item_file_id,
                            FAILED_PARSE,
                            f"Unexpected error adding queue item: {db_exc}",
                        )
                    )
                    continue

                details.append(
                    _detail(
                        "queue_item",
                        item_file_id,
                        IMPORTED,
                        f"Queue item (position={position}) added to queue '{q_name}'.",
                        created_id=new_item.id,
                    )
                )

        except Exception as exc:
            details.append(
                _detail(
                    "queue",
                    q_file_id,
                    FAILED_PARSE,
                    f"Unexpected error: {exc}",
                )
            )

    # ── 4. Commit everything ───────────────────────────────────────────────────
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database commit failed: {exc}") from exc

    # ── 5. Build summary counts ────────────────────────────────────────────────
    def _counts(obj_type: str) -> dict:
        subset = [d for d in details if d["type"] == obj_type]
        imported_n = sum(1 for d in subset if d["outcome"] == IMPORTED)
        skipped_n = sum(1 for d in subset if d["outcome"].startswith("skipped"))
        failed_n = sum(1 for d in subset if d["outcome"].startswith("failed"))
        return {"imported": imported_n, "skipped": skipped_n, "failed": failed_n}

    stage_state_present = "stage_state" in payload

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_filename": file.filename or "unknown",
        "summary": {
            "scripts": _counts("script"),
            "queues": _counts("queue"),
            "queue_items": _counts("queue_item"),
            "stage_state": "present_in_file" if stage_state_present else "absent",
        },
        "details": details,
    }
    return report
