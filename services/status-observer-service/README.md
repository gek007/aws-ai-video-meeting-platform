# Status Observer Service

Polls external providers for open task status changes.

## Current Implementation

- accepts task status payloads
- persists `external_tasks.external_status`
- updates `last_synced_at`
- returns `task.status.changed` event shape for downstream notification handling

## Current Limitation

Real scheduled polling through `EventBridge Scheduler` and provider API polling are still pending.
