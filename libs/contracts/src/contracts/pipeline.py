from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MediaProcessingRequested:
    tenant_id: str
    meeting_id: str
    video_item_id: str
    processing_job_id: str
    raw_video_bucket: str
    raw_video_key: str
    correlation_id: str


@dataclass(slots=True)
class TranscriptReady:
    tenant_id: str
    meeting_id: str
    video_item_id: str
    transcript_bucket: str
    transcript_key: str
    correlation_id: str


@dataclass(slots=True)
class ActionItem:
    title: str
    description: str
    item_type: str
    owner_email: str | None = None
    priority: str | None = None

