from transcription_service.transcriber import AmazonTranscribeClient, InMemoryTranscriber


class StubTranscribeClient:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def start_transcription_job(self, **kwargs):
        self.requests.append(kwargs)
        return {"TranscriptionJob": {"TranscriptionJobName": kwargs["TranscriptionJobName"]}}


def test_inmemory_transcriber_returns_expected_transcript_artifact():
    artifact = InMemoryTranscriber().transcribe(
        tenant_id="tenant_123",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        audio_bucket="audio-bucket",
        audio_key="tenant_123/mtg_123/vid_123/audio.wav",
        transcript_bucket="transcript-bucket",
        language_code="en-US",
        speaker_diarization=True,
        pii_redaction=False,
    )

    assert artifact.provider == "in-memory"
    assert artifact.transcript_key == "tenant_123/mtg_123/vid_123/transcript.json"


def test_amazon_transcribe_client_starts_transcription_job():
    client = StubTranscribeClient()
    artifact = AmazonTranscribeClient(
        output_bucket="transcript-bucket",
        client_factory=lambda: client,
    ).transcribe(
        tenant_id="tenant_123",
        meeting_id="mtg_123",
        video_item_id="vid_123",
        audio_bucket="audio-bucket",
        audio_key="tenant_123/mtg_123/vid_123/audio.wav",
        transcript_bucket="ignored-bucket",
        language_code="en-US",
        speaker_diarization=True,
        pii_redaction=True,
    )

    request = client.requests[0]
    assert request["Media"]["MediaFileUri"] == "s3://audio-bucket/tenant_123/mtg_123/vid_123/audio.wav"
    assert request["OutputBucketName"] == "transcript-bucket"
    assert request["OutputKey"] == "tenant_123/mtg_123/vid_123/transcript.json"
    assert request["Settings"]["ShowSpeakerLabels"] is True
    assert request["ContentRedaction"]["RedactionType"] == "PII"
    assert request["TranscriptionJobName"] == "transcribe__tenant_123__mtg_123__vid_123"
    assert artifact.provider == "amazon-transcribe"
    assert artifact.is_ready is False
