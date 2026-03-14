from __future__ import absolute_import

import io
import json
import logging
import os
import socket

from bottle import Bottle, request, response, abort, static_file

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

from app.database import engine, Base, SessionLocal
from app.routers import scripts, queues

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


class SecurityHeadersMiddleware(object):
    """WSGI middleware that adds CORS and Vary: Cookie to every response.

    Applying these headers at the WSGI layer guarantees they are present
    regardless of whether the inner handler returns a plain string, a
    Bottle HTTPResponse object, or a static file response.

    The Vary: Cookie header mirrors the fix shipped in Flask 2.2.5 / 2.3.2
    (CVE: missing Vary: Cookie on session-cookie responses).  Although this
    app does not use server-side sessions, the header is included proactively
    so that any intermediate cache never serves a stale cookie-gated response
    to the wrong client.
    """

    def __init__(self, wsgi_app):
        self.app = wsgi_app

    def __call__(self, environ, start_response):
        def _start_response(status, headers, exc_info=None):
            names = [h[0].lower() for h in headers]
            if "access-control-allow-origin" not in names:
                headers.append(("Access-Control-Allow-Origin", "*"))
            if "access-control-allow-methods" not in names:
                headers.append(("Access-Control-Allow-Methods",
                                 "GET, POST, PUT, DELETE, OPTIONS"))
            if "access-control-allow-headers" not in names:
                headers.append(("Access-Control-Allow-Headers",
                                 "Content-Type, Authorization"))
            # Vary: Cookie — merge with any existing Vary value
            vary_vals = [v for k, v in headers if k.lower() == "vary"]
            current_vary = ", ".join(vary_vals)
            if "cookie" not in current_vary.lower():
                new_vary = (current_vary + ", Cookie").lstrip(", ") if current_vary else "Cookie"
                headers = [(k, v) for k, v in headers if k.lower() != "vary"]
                headers.append(("Vary", new_vary))
            return start_response(status, headers, exc_info)

        return self.app(environ, _start_response)


Base.metadata.create_all(bind=engine)

_bottle = Bottle()

# In-memory stage state
stage_state = {
    "active_queue_id": None,
    "active_script_id": None,
    "scroll_position": 0.0,
    "auto_scroll_speed": 3.0,
    "is_scrolling": False,
}


# OPTIONS pre-flight handler for all routes
@_bottle.route("/<path:path>", method="OPTIONS")
@_bottle.route("/", method="OPTIONS")
def options_handler(path=""):
    response.content_type = "application/json"
    return "{}"


scripts.setup_routes(_bottle)
queues.setup_routes(_bottle)


@_bottle.route("/api/stage/state", method="GET")
def get_stage_state():
    response.content_type = "application/json"
    return json.dumps(stage_state)


@_bottle.route("/api/stage/state", method="POST")
def update_stage_state():
    update = request.json or {}
    for k, v in update.items():
        if k in stage_state:
            stage_state[k] = v
    response.content_type = "application/json"
    return json.dumps(stage_state)


@_bottle.route("/api/qr", method="GET")
def get_qr_code():
    if not HAS_QRCODE:
        abort(500, "qrcode library not available")
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
        response.content_type = "image/svg+xml"
        return buf.getvalue()
    except Exception:
        logger.exception("Failed to generate QR code for %s", remote_url)
        abort(500, "Failed to generate QR code")


@_bottle.route("/static/<filepath:path>")
def serve_static(filepath):
    return static_file(filepath, root=_static_dir)


@_bottle.route("/")
def read_root():
    return static_file("index.html", root=_static_dir)


@_bottle.route("/teleprompter")
def teleprompter():
    return static_file("teleprompter.html", root=_static_dir)


@_bottle.route("/remote")
def remote():
    return static_file("remote.html", root=_static_dir)


# Exported WSGI app — wrapped with security middleware
app = SecurityHeadersMiddleware(_bottle)
