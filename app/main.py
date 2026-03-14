from __future__ import absolute_import

from flask import Flask, request, jsonify, send_file, g, Response, abort
from flask_cors import CORS
from app.database import engine, Base, SessionLocal
from app.routers import scripts, queues
import io
import logging
import os
import socket

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

try:
    import qrcode
    import qrcode.image.svg
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

logger = logging.getLogger(__name__)

REMOTE_PATH = "/remote"

_static_dir = os.path.join(os.path.dirname(__file__), "static")


def get_lan_ip():
    """Return the LAN IP of this host.

    Opens a temporary UDP socket toward an external address so the OS selects
    the appropriate outgoing interface.  No data is actually transmitted.
    Falls back to '127.0.0.1' if the network is unavailable.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


Base.metadata.create_all(bind=engine)

app = Flask(__name__, static_folder=_static_dir, static_url_path="/static")
CORS(app)

# In-memory stage state
stage_state = {
    "active_queue_id": None,
    "active_script_id": None,
    "scroll_position": 0.0,
    "auto_scroll_speed": 3.0,
    "is_scrolling": False,
}


@app.before_request
def open_db():
    g.db = SessionLocal()


@app.teardown_request
def close_db(exc):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()


@app.after_request
def set_vary_cookie(response):
    # Mitigate CVE: Flask < 2.2.5 omits Vary: Cookie, which can cause
    # shared caches to serve stale session data to the wrong user.
    # This replicates the fix shipped in Flask 2.2.5 / 2.3.2.
    vary = response.headers.get("Vary", "")
    if "Cookie" not in vary:
        response.headers["Vary"] = (vary + ", Cookie").lstrip(", ") if vary else "Cookie"
    return response


app.register_blueprint(scripts.blueprint)
app.register_blueprint(queues.blueprint)


@app.route("/api/stage/state", methods=["GET"])
def get_stage_state():
    return jsonify(stage_state)


@app.route("/api/stage/state", methods=["POST"])
def update_stage_state():
    update = request.get_json() or {}
    for k, v in update.items():
        if k in stage_state:
            stage_state[k] = v
    return jsonify(stage_state)


@app.route("/api/qr")
def get_qr_code():
    if not HAS_QRCODE:
        abort(500)
    parsed = urlparse(request.url_root)
    lan_ip = get_lan_ip()
    default_ports = {"http": 80, "https": 443}
    port_num = parsed.port
    scheme = parsed.scheme
    port = ":{0}".format(port_num) if port_num and port_num != default_ports.get(scheme) else ""
    remote_url = "{0}://{1}{2}{3}".format(scheme, lan_ip, port, REMOTE_PATH)
    try:
        factory = qrcode.image.svg.SvgPathFillImage
        img = qrcode.make(remote_url, image_factory=factory)
        buf = io.BytesIO()
        img.save(buf)
        buf.seek(0)
        return Response(buf.getvalue(), mimetype="image/svg+xml")
    except Exception:
        logger.exception("Failed to generate QR code for %s", remote_url)
        abort(500)


@app.route("/")
def read_root():
    return send_file(os.path.join(_static_dir, "index.html"))


@app.route("/teleprompter")
def teleprompter():
    return send_file(os.path.join(_static_dir, "teleprompter.html"))


@app.route("/remote")
def remote():
    return send_file(os.path.join(_static_dir, "remote.html"))
