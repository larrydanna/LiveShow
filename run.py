from __future__ import absolute_import

import os
from bottle import run
from app.main import app

if __name__ == "__main__":
    debug = os.environ.get("BOTTLE_DEBUG", "0") == "1"
    run(app, host="0.0.0.0", port=8000, debug=debug, reloader=debug)
