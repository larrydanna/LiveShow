# Database

This component provides the persistent data layer for LiveShow.

## Responsibilities

- Define and manage the database schema (Scripts, ScriptQueues)
- Handle schema migrations as the data model evolves
- Expose a data-access layer consumed by the API

## Entities

### Script

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Primary key |
| `title` | string (256) | Script title |
| `body` | text | Full script content |
| `submitted_by` | string (48) | Name of the submitter |
| `created_at` | datetime | Submission timestamp |

### ScriptQueue

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Primary key |
| `name` | string | Queue name |
| `scripts` | ordered list | Ordered collection of Scripts |

## Setup

See the API component's README for instructions on how to initialise the database as part of the full application setup.
