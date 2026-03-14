"""
Serialization helpers that convert SQLAlchemy model instances to plain dicts.
This replaces the Pydantic v2 schemas so the codebase runs on Python 2.7.
"""


def _iso(dt):
    return dt.isoformat() if dt is not None else None


# ---------------------------------------------------------------------------
# Script serializers
# ---------------------------------------------------------------------------

def script_list_item(script):
    return {
        "id": script.id,
        "title": script.title,
        "submitted_by": script.submitted_by,
        "created_at": _iso(script.created_at),
    }


def script_detail(script):
    data = script_list_item(script)
    data["body"] = script.body
    return data


# ---------------------------------------------------------------------------
# Queue serializers
# ---------------------------------------------------------------------------

def queue_list_item(queue):
    return {
        "id": queue.id,
        "name": queue.name,
        "created_at": _iso(queue.created_at),
    }


def queue_item_schema(item, script):
    return {
        "id": item.id,
        "script_id": item.script_id,
        "position": item.position,
        "script": script_list_item(script),
    }


def queue_detail(queue, script_items):
    return {
        "id": queue.id,
        "name": queue.name,
        "created_at": _iso(queue.created_at),
        "scripts": script_items,
    }
