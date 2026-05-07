# Notification Service

Formats outbound notifications, persists notification metadata, and can deliver email through Amazon SES.

## Current Implementation

- renders notification message and subject from templates
- persists delivery records in `notifications`
- supports:
  - `InMemoryNotificationSender`
  - `SESNotificationSender`

## Still Planned

- Slack delivery
- Teams delivery
- retry and DLQ behavior
