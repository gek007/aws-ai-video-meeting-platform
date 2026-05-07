from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from shared.ids import new_id


@dataclass(frozen=True, slots=True)
class UploadSession:
    meeting_id: str
    video_item_id: str
    upload_url: str
    s3_bucket: str
    s3_key: str
    expires_in: int
    method: str
    fields: dict


class InMemoryUploader:
    """Returns a deterministic fake pre-signed URL for tests and local development."""

    def create_upload_session(
        self,
        *,
        filename: str,
        tenant_id: str,
        content_type: str = "video/mp4",
        expires_in: int = 3600,
    ) -> UploadSession:
        meeting_id = new_id("mtg")
        video_item_id = new_id("vid")
        bucket = "raw-video-bucket-local"
        key = f"{tenant_id}/{meeting_id}/{video_item_id}/{filename}"
        return UploadSession(
            meeting_id=meeting_id,
            video_item_id=video_item_id,
            upload_url=f"https://uploads.example.com/{bucket}/{key}",
            s3_bucket=bucket,
            s3_key=key,
            expires_in=expires_in,
            method="PUT",
            fields={},
        )


class S3PresignedUploader:
    """Generates a real AWS S3 pre-signed PUT URL for direct browser uploads."""

    def __init__(
        self,
        bucket: str | None = None,
        client_factory: Callable[[], object] | None = None,
    ) -> None:
        self._bucket = bucket or os.getenv("RAW_VIDEO_BUCKET")
        if not self._bucket and client_factory is None:
            raise ValueError("RAW_VIDEO_BUCKET is required for S3PresignedUploader.")
        self._client_factory = client_factory

    def create_upload_session(
        self,
        *,
        filename: str,
        tenant_id: str,
        content_type: str = "video/mp4",
        expires_in: int = 3600,
    ) -> UploadSession:
        meeting_id = new_id("mtg")
        video_item_id = new_id("vid")
        key = f"{tenant_id}/{meeting_id}/{video_item_id}/{filename}"

        url = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": key,
                "ContentType": content_type,
                "Metadata": {
                    "tenant-id": tenant_id,
                    "meeting-id": meeting_id,
                    "video-item-id": video_item_id,
                },
            },
            ExpiresIn=expires_in,
        )

        return UploadSession(
            meeting_id=meeting_id,
            video_item_id=video_item_id,
            upload_url=url,
            s3_bucket=self._bucket,
            s3_key=key,
            expires_in=expires_in,
            method="PUT",
            fields={},
        )

    @property
    def _client(self):
        if self._client_factory is not None:
            return self._client_factory()
        import boto3
        return boto3.client("s3")
