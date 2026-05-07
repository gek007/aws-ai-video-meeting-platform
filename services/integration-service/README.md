# Integration Service

Creates external tasks in provider systems.

## Current Implementation

- supports provider abstraction for external issue systems
- includes `Jira` and `GitHub Issues` connectors
- persists created tasks into `external_tasks`
- returns `external.task.created` events for downstream use

## Still Planned

- duplicate prevention against repeated task creation
- provider-specific rate limit and retry handling
- broader provider coverage
