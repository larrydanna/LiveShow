from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from app.database import engine, Base
from app.routers import scripts, queues
import io
import logging
import os
import socket
import urllib.parse
import qrcode
import qrcode.image.svg

logger = logging.getLogger(__name__)

REMOTE_PATH = "/remote"


def get_lan_ip() -> str:
    """Return the LAN IP of this host.

    Opens a temporary UDP socket toward an external address so the OS selects
    the appropriate outgoing interface.  No data is actually transmitted.
    Falls back to '127.0.0.1' if the network is unavailable.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


Base.metadata.create_all(bind=engine)

app = FastAPI(title="LiveShow Teleprompter", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stage state
stage_state = {
    "active_queue_id": None,
    "active_script_id": None,
    "scroll_position": 0.0,
    "auto_scroll_speed": 3.0,
    "is_scrolling": False,
}

app.include_router(scripts.router)
app.include_router(queues.router)

stage_router = APIRouter(prefix="/api/stage", tags=["stage"])


@stage_router.get("/state")
def get_stage_state():
    return stage_state


@stage_router.post("/state")
def update_stage_state(update: dict):
    stage_state.update({k: v for k, v in update.items() if k in stage_state})
    return stage_state


app.include_router(stage_router)

static_dir = os.path.join(os.path.dirname(__file__), "static")


@app.get("/api/qr")
def get_qr_code(request: Request):
    parsed = urllib.parse.urlparse(str(request.base_url))
    lan_ip = get_lan_ip()
    default_ports = {"http": 80, "https": 443}
    port = (
        f":{parsed.port}"
        if parsed.port and parsed.port != default_ports.get(parsed.scheme)
        else ""
    )
    remote_url = f"{parsed.scheme}://{lan_ip}{port}{REMOTE_PATH}"
    try:
        factory = qrcode.image.svg.SvgPathFillImage
        img = qrcode.make(remote_url, image_factory=factory)
        buf = io.BytesIO()
        img.save(buf)
        buf.seek(0)
        return Response(content=buf.getvalue(), media_type="image/svg+xml")
    except Exception:
        logger.exception("Failed to generate QR code for %s", remote_url)
        return Response(status_code=500)


app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/teleprompter")
def teleprompter():
    return FileResponse(os.path.join(static_dir, "teleprompter.html"))


@app.get("/remote")
def remote():
    return FileResponse(os.path.join(static_dir, "remote.html"))
