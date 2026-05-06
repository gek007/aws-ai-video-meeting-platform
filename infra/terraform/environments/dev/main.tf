terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "platform" {
  source               = "../../modules/platform"
  project_name         = var.project_name
  environment          = var.environment
  raw_video_bucket     = "${var.project_name}-${var.environment}-raw-video"
  audio_bucket         = "${var.project_name}-${var.environment}-audio"
  transcript_bucket    = "${var.project_name}-${var.environment}-transcript"
  artifacts_bucket     = "${var.project_name}-${var.environment}-artifacts"
  meeting_topic_name   = "${var.project_name}-${var.environment}-meeting-intelligence"
  media_queue_name     = "${var.project_name}-${var.environment}-media-processing"
  transcription_queue  = "${var.project_name}-${var.environment}-transcription"
  enrichment_queue     = "${var.project_name}-${var.environment}-ai-enrichment"
  task_queue           = "${var.project_name}-${var.environment}-task-creation"
  notification_queue   = "${var.project_name}-${var.environment}-notifications"
}

