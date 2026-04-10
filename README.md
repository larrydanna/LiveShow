# LiveShow
Teleprompter application to provide real time text for a live stage performance.

## Overview

LiveShow is a multi-tier teleprompter application designed for live stage environments. It runs on-premises on common hardware and supports PC, Apple Mac, and Linux.

## Maintenance Workflow

- **GitHub Issue**: Create an issue at GitHub
- **Assign to Agent**: Assign the issue to an agent
- **Wait for Pull Request**: Let the agent submit a pull request
- **Pull the Lates**: Pull the branch locally and test it
- **Iterate (Optional)** Respond with comments and repeat
- **Approve the Pull Request** Once approved, pull the repo and verify on `main` 

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
- **Settings tab**: Configure instance name and foot pedal key-to-action mappings

## Foot Pedal (HID Keyboard) Support

LiveShow supports USB foot pedals that operate as HID keyboards (they send keystrokes when pressed).

### Tested Hardware
- **Ikkegol 3-button USB pedal** — left pedal sends `a`, center pedal sends `b`, right pedal sends `c` by default.
- Any USB HID keyboard pedal with configurable or fixed key output.

### Default Mapping
| Pedal | Key | Default Action |
|-------|-----|----------------|
| Left | `a` | *(none)* |
| Center | `b` | Toggle Start/Stop scrolling |
| Right | `c` | *(none)* |

### Configuring Pedal Mappings
1. Open the **Remote Management** page (`http://localhost:8000/remote`).
2. Navigate to the **Settings** tab.
3. Under **Foot Pedal Mappings**, each row specifies:
   - **Key** — the character your pedal sends (e.g., `a`, `b`, `c`).
   - **Action** — what the teleprompter should do when that key is received.
4. Available actions:
   - *No action* — pedal press is ignored.
   - **Toggle Start/Stop scrolling** — start or stop auto-scroll.
   - **Scroll up 50px** — nudge the view up.
   - **Scroll down 50px** — nudge the view down.
   - **Page up** — jump up by one full screen height.
   - **Page down** — jump down by one full screen height.
5. Use **+ Add Mapping** to add rows for additional pedal buttons or keys.
6. Click **Save Pedal Mappings** to persist your configuration.

> **Tip:** Pedal mappings are active only in the **Teleprompter View** (`/teleprompter`). The settings take effect immediately after saving — no page reload is required for a newly opened teleprompter session.

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
| GET | `/api/config` | Get instance configuration |
| PUT | `/api/config` | Update instance configuration |
| GET | `/api/config/pedal-mappings` | Get foot pedal key-to-action mappings |
| PUT | `/api/config/pedal-mappings` | Update foot pedal key-to-action mappings |

Interactive API docs are available at `http://localhost:8000/docs`.

## Database

SQLite database is created automatically at `./liveshow.db` on first run.

### Schema
- **Script**: `id`, `title` (max 256 chars), `body`, `submitted_by` (max 48 chars), `font_face` (max 256 chars, optional), `font_size` (max 64 chars, optional), `created_at`
- **ScriptQueue**: `id`, `name` (max 256 chars, unique), `created_at`
- **ScriptQueueItem**: `id`, `queue_id`, `script_id`, `position` (ordering within queue)

