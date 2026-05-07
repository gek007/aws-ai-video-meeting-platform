# Task Orchestrator Service

Transforms extracted action items into integration-ready work requests.

## Current Implementation

- accepts `meeting.intelligence.generated`-style action item payloads
- ensures each outgoing item has an `actionItemId`
- returns `task.creation.requested` for the integration layer
