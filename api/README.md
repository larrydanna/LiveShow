# API

This component exposes a RESTful Web Service API for all LiveShow clients.

## Responsibilities

- Provide HTTP endpoints for Script and ScriptQueue management
- Mediate all access to the Database component
- Serve as the single integration point for both UI clients

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/scripts` | List all scripts |
| `POST` | `/scripts` | Submit a new script |
| `GET` | `/queues` | List all script queues |
| `POST` | `/queues/{id}/scripts` | Add a script to a queue |

## Setup

_Instructions will be added when the implementation is in place._

## Running

_Instructions will be added when the implementation is in place._
