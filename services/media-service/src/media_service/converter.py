from __future__ import annotations

import os
import subprocess
import uuid
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True, slots=True)
class ConversionArtifact:
    audio_bucket: str
    audio_key: str
    is_ready: bool
    job_id: str
    engine: str


@dataclass(slots=True)
class InMemoryConverter:
    """Deterministic in-memory converter for tests and local development."""

    conversions: list[dict] = field(default_factory=list)

    def convert(
        self,
        *,
        source_bucket: str,
        source_key: str,
        output_bucket: str,
        output_key: str,
        tenant_id: str = "",
        meeting_id: str = "",
        video_item_id: str = "",
        correlation_id: str | None = None,
    ) -> ConversionArtifact:
        job_id = f"in-memory-{len(self.conversions) + 1}"
        self.conversions.append(
            {
                "sourceBucket": source_bucket,
                "sourceKey": source_key,
                "outputBucket": output_bucket,
                "outputKey": output_key,
                "jobId": job_id,
                "tenantId": tenant_id,
                "meetingId": meeting_id,
                "videoItemId": video_item_id,
            }
        )
        return ConversionArtifact(
            audio_bucket=output_bucket,
            audio_key=output_key,
            is_ready=True,
            job_id=job_id,
            engine="in-memory",
        )


class FFmpegSubprocessConverter:
    """Runs ffmpeg as a subprocess.

    Requires ffmpeg on PATH or provided via an AWS Lambda layer.
    Reads directly from S3 when the source URL is s3://, otherwise expects a local path.
    """

    def __init__(
        self,
        ffmpeg_path: str | None = None,
        s3_client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._ffmpeg_path = ffmpeg_path or os.getenv("FFMPEG_PATH", "ffmpeg")
        self._s3_client_factory = s3_client_factory

    def convert(
        self,
        *,
        source_bucket: str,
        source_key: str,
        output_bucket: str,
        output_key: str,
        tenant_id: str = "",
        meeting_id: str = "",
        video_item_id: str = "",
        correlation_id: str | None = None,
    ) -> ConversionArtifact:
        tmp_input = f"/tmp/{uuid.uuid4()}_input"
        tmp_output = f"/tmp/{uuid.uuid4()}.wav"

        self._s3.download_file(source_bucket, source_key, tmp_input)

        subprocess.run(
            [
                self._ffmpeg_path,
                "-y",
                "-i", tmp_input,
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-vn",
                tmp_output,
            ],
            check=True,
            timeout=600,
            capture_output=True,
        )

        self._s3.upload_file(tmp_output, output_bucket, output_key)

        return ConversionArtifact(
            audio_bucket=output_bucket,
            audio_key=output_key,
            is_ready=True,
            job_id=str(uuid.uuid4()),
            engine="ffmpeg",
        )

    @property
    def _s3(self):
        if self._s3_client_factory is not None:
            return self._s3_client_factory()
        import boto3
        return boto3.client("s3")


class MediaConvertAdapter:
    """Submits an AWS MediaConvert job and returns immediately.

    The conversion is asynchronous. When complete, MediaConvert emits an
    EventBridge event that must be handled by MediaConversionCompletionService.
    """

    def __init__(
        self,
        role_arn: str | None = None,
        queue_arn: str | None = None,
        endpoint_url: str | None = None,
        client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._role_arn = role_arn or os.getenv("MEDIACONVERT_ROLE_ARN")
        self._queue_arn = queue_arn or os.getenv("MEDIACONVERT_QUEUE_ARN")
        self._endpoint_url = endpoint_url or os.getenv("MEDIACONVERT_ENDPOINT")
        if not self._role_arn and client_factory is None:
            raise ValueError("MEDIACONVERT_ROLE_ARN is required for MediaConvertAdapter.")
        self._client_factory = client_factory

    def convert(
        self,
        *,
        source_bucket: str,
        source_key: str,
        output_bucket: str,
        output_key: str,
        tenant_id: str = "",
        meeting_id: str = "",
        video_item_id: str = "",
        correlation_id: str | None = None,
    ) -> ConversionArtifact:
        output_prefix = output_key.rsplit("/", 1)[0] + "/"
        create_kwargs: dict = {
            "Role": self._role_arn,
            "Settings": self._build_job_settings(
                source_bucket=source_bucket,
                source_key=source_key,
                output_bucket=output_bucket,
                output_prefix=output_prefix,
            ),
            "UserMetadata": {
                "outputBucket": output_bucket,
                "outputKey": output_key,
                "tenantId": tenant_id,
                "meetingId": meeting_id,
                "videoItemId": video_item_id,
                **({"correlationId": correlation_id} if correlation_id else {}),
            },
        }
        if self._queue_arn:
            create_kwargs["Queue"] = self._queue_arn

        response = self._client.create_job(**create_kwargs)
        return ConversionArtifact(
            audio_bucket=output_bucket,
            audio_key=output_key,
            is_ready=False,
            job_id=response["Job"]["Id"],
            engine="mediaconvert",
        )

    def _build_job_settings(
        self,
        *,
        source_bucket: str,
        source_key: str,
        output_bucket: str,
        output_prefix: str,
    ) -> dict:
        return {
            "Inputs": [
                {
                    "FileInput": f"s3://{source_bucket}/{source_key}",
                    "AudioSelectors": {
                        "Audio Selector 1": {"DefaultSelection": "DEFAULT"}
                    },
                }
            ],
            "OutputGroups": [
                {
                    "Name": "File Group",
                    "OutputGroupSettings": {
                        "Type": "FILE_GROUP_SETTINGS",
                        "FileGroupSettings": {
                            "Destination": f"s3://{output_bucket}/{output_prefix}",
                        },
                    },
                    "Outputs": [
                        {
                            "NameModifier": "audio",
                            "ContainerSettings": {"Container": "RAW"},
                            "AudioDescriptions": [
                                {
                                    "AudioTypeControl": "FOLLOW_INPUT",
                                    "CodecSettings": {
                                        "Codec": "WAV",
                                        "WavSettings": {
                                            "Channels": 1,
                                            "SampleRate": 16000,
                                            "BitDepth": 16,
                                        },
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        }

    @property
    def _client(self):
        if self._client_factory is not None:
            return self._client_factory()
        import boto3
        if not self._endpoint_url:
            mc = boto3.client("mediaconvert", region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = mc.describe_endpoints(Mode="DEFAULT")
            self._endpoint_url = response["Endpoints"][0]["Url"]
        return boto3.client("mediaconvert", endpoint_url=self._endpoint_url)
