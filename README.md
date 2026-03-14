# LiveShow

Teleprompter application to provide real time text for a live stage performance.

## Overview

LiveShow is a multi-tier application designed to run on-premises on common mid-level hardware (PC, Mac, and Linux). Each component is a separate concern that can be deployed together on a single workstation or distributed across multiple hosts.

## Project Structure

```
LiveShow/
├── docs/                       # Architecture documentation and design decisions
├── database/                   # Data layer – schema, migrations, and data access
├── api/                        # Web Service API – REST endpoints for all clients
└── ui/
    ├── on-stage/               # 10-foot On-Stage UI (teleprompter display)
    └── remote-management/      # Mobile-friendly Remote Management UI
```

## Components

| Component | Directory | Description |
|-----------|-----------|-------------|
| Database | `database/` | SQLite-backed data store for Scripts and ScriptQueues |
| API | `api/` | REST API exposing Script and Queue management endpoints |
| On-Stage UI | `ui/on-stage/` | Full-screen teleprompter display with paging and auto-scroll |
| Remote Management UI | `ui/remote-management/` | Mobile-friendly interface for managing scripts and queues |

## Getting Started

See each component's `README.md` for setup and run instructions.

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed architectural decisions and component interactions.
