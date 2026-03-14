# LiveShow
Teleprompter application to provide real time text for a live stage performance.

## Overview

LiveShow is a multi-tier teleprompter application designed for live stage environments. It runs on-premises on common hardware and supports PC, Apple Mac, and Linux.

## Architecture

- **Database**: SQLite (embedded, no server required)
- **API**: Python FastAPI REST service
- **UI**: Browser-based, served by the API server
  - On-Stage 10-foot display (queue/script selection + teleprompter)
  - Remote Management (mobile-friendly, for backstage control)

## Requirements

- Python 3.10+

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python run.py
```

The application starts on `http://0.0.0.0:8000`. Open a browser and navigate to:

- `http://localhost:8000/` — **On-Stage UI** (10-foot display: select queue, select script, launch teleprompter)
- `http://localhost:8000/teleprompter?script_id=<id>` — **Teleprompter View**
- `http://localhost:8000/remote` — **Remote Management** (scripts, queues, stage control)

## Features

### On-Stage UI (`/`)
- Dark theme optimized for 10-foot viewing distance
- Two-panel layout: Queues on the left, Scripts on the right
- Keyboard navigation: Arrow keys to move selection, Enter to confirm, Esc to go back
- Click **Launch Teleprompter** or press Enter on a script to open the teleprompter view

### Teleprompter View (`/teleprompter`)
- Large serif text (2.5rem) on a black background
- **Auto-scroll** using `requestAnimationFrame` for smooth performance
- **Speed slider**: 1–10 scale (maps to 20–200 px/sec)
- **Keyboard shortcuts**:
  - `Space` — Start/pause auto-scroll
  - `↑` / `↓` — Manual scroll 50px
  - `PageUp` / `PageDown` — Jump by full page
  - `Esc` — Return to the On-Stage UI
- **Remote sync**: polls `/api/stage/state` every 2 seconds so the Remote Management UI can control the display

### Remote Management (`/remote`)
- Mobile-friendly responsive layout (works on phones/tablets)
- **Scripts tab**: Add new scripts (title, body, submitted by), list and delete scripts
- **Queues tab**: Create, rename, delete queues; add/remove/reorder scripts within a queue
- **Stage Control tab**: Select active queue/script, toggle auto-scroll, adjust speed, page up/down

## REST API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/scripts` | List all scripts |
| POST | `/api/scripts` | Create a script |
| GET | `/api/scripts/{id}` | Get a script (with body) |
| PUT | `/api/scripts/{id}` | Update a script |
| DELETE | `/api/scripts/{id}` | Delete a script |
| GET | `/api/queues` | List all queues |
| POST | `/api/queues` | Create a queue |
| GET | `/api/queues/{id}` | Get queue with ordered scripts |
| PUT | `/api/queues/{id}` | Rename a queue |
| DELETE | `/api/queues/{id}` | Delete a queue |
| POST | `/api/queues/{id}/scripts` | Add a script to a queue |
| DELETE | `/api/queues/{id}/scripts/{sid}` | Remove a script from a queue |
| PUT | `/api/queues/{id}/scripts/reorder` | Reorder scripts in a queue |
| GET | `/api/stage/state` | Get current stage state |
| POST | `/api/stage/state` | Update stage state (remote control) |

Interactive API docs are available at `http://localhost:8000/docs`.

## Database

SQLite database is created automatically at `./liveshow.db` on first run.

### Schema
- **Script**: `id`, `title` (max 256 chars), `body`, `submitted_by` (max 48 chars), `created_at`
- **ScriptQueue**: `id`, `name` (max 256 chars, unique), `created_at`
- **ScriptQueueItem**: `id`, `queue_id`, `script_id`, `position` (ordering within queue)

