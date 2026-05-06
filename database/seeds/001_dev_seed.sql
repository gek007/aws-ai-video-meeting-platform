INSERT INTO meetings (id, tenant_id, source_type, title, organizer_email, status)
VALUES ('mtg_seed_001', 'tenant_demo', 'manual_upload', 'Demo Platform Planning', 'owner@example.com', 'pending')
ON CONFLICT (id) DO NOTHING;

INSERT INTO video_items (id, tenant_id, meeting_id, source_type, original_filename, s3_bucket, s3_key, upload_status, processing_status, transcription_status, ai_enrichment_status)
VALUES ('vid_seed_001', 'tenant_demo', 'mtg_seed_001', 'manual_upload', 'demo-meeting.mp4', 'raw-video-bucket', 'tenant_demo/demo-meeting.mp4', 'uploaded', 'queued', 'pending', 'pending')
ON CONFLICT (id) DO NOTHING;

INSERT INTO tenant_integrations (id, tenant_id, provider, config_reference, status)
VALUES ('int_seed_jira', 'tenant_demo', 'jira', 'secret://tenant_demo/jira', 'active')
ON CONFLICT (id) DO NOTHING;

