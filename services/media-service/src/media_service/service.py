from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from contracts.validation import require_keys
from media_service.converter import ConversionArtifact
from shared.events import base_event


class QueuePublisher(Protocol):
    def publish_transcription_request(self, payload: dict) -> None: ...


class MetadataStore(Protocol):
    def record_audio_artifact(
        self,
        *,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        audio_bucket: str,
        audio_key: str,
        conversion_engine: str,
    ) -> None: ...


class VideoConverter(Protocol):
    def convert(
        self,
        *,
        source_bucket: str,
        source_key: str,
        output_bucket: str,
        output_key: str,
        tenant_id: str,
        meeting_id: str,
        video_item_id: str,
        correlation_id: str | None,
    ) -> ConversionArtifact: ...


@dataclass(slots=True)
class MediaProcessingResult:
    next_event: dict


class MediaService:
    def __init__(
        self,
        publisher: QueuePublisher,
        metadata_store: MetadataStore,
        converter: VideoConverter | None = None,
    ) -> None:
        self._publisher = publisher
        self._metadata_store = metadata_store
        self._converter = converter

    def process(self, event: dict) -> MediaProcessingResult:
        require_keys(event, ["rawVideo", "tenantId", "meetingId", "videoItemId", "correlationId"])
        raw_video = event["rawVideo"]
        output_bucket = event.get("audioOutputBucket", "audio-bucket")
        output_key = f'{event["tenantId"]}/{event["meetingId"]}/{event["videoItemId"]}/audio.wav'

        if self._converter is not None:
            artifact = self._converter.convert(
                source_bucket=raw_video["bucket"],
                source_key=raw_video["key"],
                output_bucket=output_bucket,
                output_key=output_key,
                tenant_id=event["tenantId"],
                meeting_id=event["meetingId"],
                video_item_id=event["videoItemId"],
                correlation_id=event.get("correlationId"),
            )
        else:
            artifact = ConversionArtifact(
                audio_bucket=output_bucket,
                audio_key=output_key,
                is_ready=True,
                job_id="no-converter",
                engine=event.get("conversionEngine", "mediaconvert"),
            )

        if not artifact.is_ready:
            next_event = base_event(
                "media.conversion.job.started",
                tenant_id=event["tenantId"],
                meeting_id=event["meetingId"],
                video_item_id=event["videoItemId"],
                correlation_id=event["correlationId"],
            )
            next_event["conversionJobId"] = artifact.job_id
            next_event["conversionEngine"] = artifact.engine
            next_event["expectedAudio"] = {
                "bucket": artifact.audio_bucket,
                "key": artifact.audio_key,
            }
            return MediaProcessingResult(next_event=next_event)

        next_event = self._build_transcription_event(event, artifact)
        self._metadata_store.record_audio_artifact(
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            audio_bucket=artifact.audio_bucket,
            audio_key=artifact.audio_key,
            conversion_engine=artifact.engine,
        )
        self._publisher.publish_transcription_request(next_event)
        return MediaProcessingResult(next_event=next_event)

    def _build_transcription_event(self, event: dict, artifact: ConversionArtifact) -> dict:
        next_event = base_event(
            "transcription.requested",
            tenant_id=event["tenantId"],
            meeting_id=event["meetingId"],
            video_item_id=event["videoItemId"],
            correlation_id=event["correlationId"],
        )
        next_event["sourceVideo"] = {
            "bucket": event["rawVideo"]["bucket"],
            "key": event["rawVideo"]["key"],
        }
        next_event["audio"] = {
            "bucket": artifact.audio_bucket,
            "key": artifact.audio_key,
            "format": "wav",
            "sampleRateHz": 16000,
            "channels": 1,
        }
        next_event["conversion"] = {
            "engine": artifact.engine,
            "jobId": artifact.job_id,
            "status": "completed",
            "targetProfile": "transcribe-optimized",
        }
        return next_event


class MediaConversionCompletionService:
    """Handles the EventBridge completion callback from an async MediaConvert job."""

    def __init__(self, publisher: QueuePublisher, metadata_store: MetadataStore) -> None:
        self._publisher = publisher
        self._metadata_store = metadata_store

    def complete(self, event: dict) -> MediaProcessingResult:
        detail = event.get("detail", {})
        status = event.get("status") or detail.get("status") or detail.get("Status")
        job_id = event.get("jobId") or detail.get("jobId") or detail.get("JobId")

        if not job_id:
            raise ValueError("jobId or detail.JobId is required in the MediaConvert completion event.")

        user_metadata = detail.get("userMetadata", event.get("userMetadata", {}))
        ids = self._resolve_ids(event, user_metadata)

        if status not in ("COMPLETE", "COMPLETED"):
            next_event = base_event(
                "media.conversion.job.failed",
                tenant_id=ids["tenantId"],
                meeting_id=ids["meetingId"],
                video_item_id=ids["videoItemId"],
                correlation_id=ids.get("correlationId"),
            )
            next_event["conversionJobId"] = job_id
            next_event["conversionEngine"] = event.get("conversionEngine", "mediaconvert")
            next_event["failedStatus"] = status
            return MediaProcessingResult(next_event=next_event)

        audio_bucket = user_metadata.get("outputBucket", event.get("audioBucket", "audio-bucket"))
        audio_key = (
            user_metadata.get("outputKey")
            or f'{ids["tenantId"]}/{ids["meetingId"]}/{ids["videoItemId"]}/audio.wav'
        )
        engine = event.get("conversionEngine", "mediaconvert")

        next_event = base_event(
            "transcription.requested",
            tenant_id=ids["tenantId"],
            meeting_id=ids["meetingId"],
            video_item_id=ids["videoItemId"],
            correlation_id=ids.get("correlationId"),
        )
        next_event["sourceVideo"] = event.get("sourceVideo", {})
        next_event["audio"] = {
            "bucket": audio_bucket,
            "key": audio_key,
            "format": "wav",
            "sampleRateHz": 16000,
            "channels": 1,
        }
        next_event["conversion"] = {
            "engine": engine,
            "jobId": job_id,
            "status": "completed",
            "targetProfile": "transcribe-optimized",
        }

        self._metadata_store.record_audio_artifact(
            tenant_id=ids["tenantId"],
            meeting_id=ids["meetingId"],
            video_item_id=ids["videoItemId"],
            audio_bucket=audio_bucket,
            audio_key=audio_key,
            conversion_engine=engine,
        )
        self._publisher.publish_transcription_request(next_event)
        return MediaProcessingResult(next_event=next_event)

    def _resolve_ids(self, event: dict, user_metadata: dict) -> dict:
        tenant_id = user_metadata.get("tenantId") or event.get("tenantId", "")
        meeting_id = user_metadata.get("meetingId") or event.get("meetingId", "")
        video_item_id = user_metadata.get("videoItemId") or event.get("videoItemId", "")
        correlation_id = user_metadata.get("correlationId") or event.get("correlationId")
        if not (tenant_id and meeting_id and video_item_id):
            raise ValueError(
                "tenantId, meetingId, and videoItemId must be present in userMetadata or event. "
                "Ensure MediaConvertAdapter stores them in UserMetadata at job submission."
            )
        return {
            "tenantId": tenant_id,
            "meetingId": meeting_id,
            "videoItemId": video_item_id,
            "correlationId": correlation_id,
        }
