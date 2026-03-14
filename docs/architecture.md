# LiveShow – Architecture

## Overview

LiveShow is a multi-tier application built around three separated concerns:

```
┌──────────────────────────────────────────────────────┐
│                        Clients                       │
│   ┌─────────────────┐     ┌────────────────────────┐ │
│   │  On-Stage UI    │     │ Remote Management UI   │ │
│   │  (10-foot view) │     │ (mobile-friendly)      │ │
│   └────────┬────────┘     └───────────┬────────────┘ │
└────────────┼──────────────────────────┼──────────────┘
             │           HTTP           │
             ▼                          ▼
┌─────────────────────────────────────────────────────┐
│                    Web Service API                  │
│           (REST – Scripts & ScriptQueues)           │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                      Database                       │
│              (Scripts, ScriptQueues)                │
└─────────────────────────────────────────────────────┘
```

## Components

### Database (`database/`)

Provides persistent storage for all application data.

**Entities:**
- **Script** – `title` (256 chars), `body`, `submitted_by` (48 chars), `created_at`
- **ScriptQueue** – named, ordered collection of Scripts

### API (`api/`)

RESTful Web Service that exposes all data operations to UI clients.

**Endpoints:**
- `GET /scripts` – List all scripts
- `POST /scripts` – Submit a new script
- `GET /queues` – List all script queues
- `POST /queues/{id}/scripts` – Add a script to a queue

### On-Stage UI (`ui/on-stage/`)

Full-screen, keyboard-driven teleprompter display for live stage use.

**Features:**
- Select a ScriptQueue and Script to display
- Teleprompter view with paging controls
- Automatic scrolling with speed adjustment
- Keyboard navigation
- Escape back to queue selection

### Remote Management UI (`ui/remote-management/`)

Mobile-friendly interface for operators to manage content and control the stage display.

**Features:**
- Post a new Script
- Create, edit, and delete ScriptQueues
- Remote page/scroll control of the On-Stage view

## Deployment

All components are designed to run on a single workstation or be distributed across multiple hosts. Communication between components uses standard HTTP so any component can be replaced or scaled independently.

**Supported platforms:** Windows, macOS, Linux
