CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_external_id TEXT,
    title TEXT,
    organizer_email TEXT,
    scheduled_start_at TIMESTAMPTZ,
    recorded_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS video_items (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    source_external_id TEXT,
    original_filename TEXT,
    s3_bucket TEXT NOT NULL,
    s3_key TEXT NOT NULL,
    file_size_bytes BIGINT,
    mime_type TEXT,
    video_codec TEXT,
    audio_codec TEXT,
    duration_seconds INTEGER,
    width INTEGER,
    height INTEGER,
    frame_rate NUMERIC(6,2),
    language_hint TEXT,
    checksum TEXT,
    upload_status TEXT NOT NULL DEFAULT 'pending',
    processing_status TEXT NOT NULL DEFAULT 'queued',
    transcription_status TEXT NOT NULL DEFAULT 'pending',
    ai_enrichment_status TEXT NOT NULL DEFAULT 'pending',
    audio_s3_key TEXT,
    transcript_s3_key TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS participants (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    email TEXT NOT NULL,
    display_name TEXT,
    role TEXT,
    attended BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transcripts (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    video_item_id TEXT NOT NULL REFERENCES video_items(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    language_code TEXT,
    transcript_s3_key TEXT NOT NULL,
    speaker_count INTEGER,
    confidence_score NUMERIC(5,4),
    redaction_applied BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS summaries (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    video_item_id TEXT NOT NULL REFERENCES video_items(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    summary_type TEXT NOT NULL,
    model_id TEXT,
    prompt_version TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    video_item_id TEXT NOT NULL REFERENCES video_items(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    label TEXT NOT NULL,
    start_offset_seconds INTEGER,
    end_offset_seconds INTEGER,
    confidence_score NUMERIC(5,4)
);

CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    video_item_id TEXT NOT NULL REFERENCES video_items(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    description TEXT NOT NULL,
    owner_email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS action_items (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    video_item_id TEXT NOT NULL REFERENCES video_items(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    item_type TEXT NOT NULL,
    owner_email TEXT,
    priority TEXT,
    due_date TIMESTAMPTZ,
    source_excerpt TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    confidence_score NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS external_tasks (
    id TEXT PRIMARY KEY,
    action_item_id TEXT NOT NULL REFERENCES action_items(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    provider_project_key TEXT,
    external_id TEXT NOT NULL,
    external_url TEXT,
    external_status TEXT,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS processing_jobs (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    video_item_id TEXT NOT NULL REFERENCES video_items(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    error_code TEXT,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    meeting_id TEXT REFERENCES meetings(id) ON DELETE SET NULL,
    video_item_id TEXT REFERENCES video_items(id) ON DELETE SET NULL,
    recipient TEXT NOT NULL,
    channel TEXT NOT NULL,
    template_name TEXT NOT NULL,
    status TEXT NOT NULL,
    sent_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS tenant_integrations (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    config_reference TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    created_by TEXT NOT NULL,
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    message_text TEXT NOT NULL,
    response_metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transcript_chunks (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    video_item_id TEXT NOT NULL REFERENCES video_items(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    start_offset_seconds INTEGER,
    end_offset_seconds INTEGER,
    embedding_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meetings_tenant_id ON meetings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_video_items_meeting_id ON video_items(meeting_id);
CREATE INDEX IF NOT EXISTS idx_video_items_tenant_status ON video_items(tenant_id, processing_status, transcription_status, ai_enrichment_status);
CREATE INDEX IF NOT EXISTS idx_action_items_meeting_id ON action_items(meeting_id);
CREATE INDEX IF NOT EXISTS idx_external_tasks_status ON external_tasks(provider, external_status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(job_type, status);
CREATE INDEX IF NOT EXISTS idx_transcript_chunks_lookup ON transcript_chunks(meeting_id, video_item_id, chunk_index);

