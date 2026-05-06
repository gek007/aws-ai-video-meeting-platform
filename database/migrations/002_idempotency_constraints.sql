ALTER TABLE video_items
    ADD CONSTRAINT uq_video_items_tenant_object UNIQUE (tenant_id, s3_bucket, s3_key);

ALTER TABLE processing_jobs
    ADD CONSTRAINT uq_processing_jobs_unique UNIQUE (meeting_id, video_item_id, job_type);

ALTER TABLE external_tasks
    ADD CONSTRAINT uq_external_tasks_unique UNIQUE (action_item_id, provider, external_id);

ALTER TABLE notifications
    ADD CONSTRAINT uq_notifications_unique UNIQUE (tenant_id, meeting_id, recipient, template_name);

