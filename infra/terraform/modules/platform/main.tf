terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

resource "aws_s3_bucket" "raw_video" {
  bucket = var.raw_video_bucket
}

resource "aws_s3_bucket" "audio" {
  bucket = var.audio_bucket
}

resource "aws_s3_bucket" "transcript" {
  bucket = var.transcript_bucket
}

resource "aws_s3_bucket" "artifacts" {
  bucket = var.artifacts_bucket
}

resource "aws_sns_topic" "meeting_intelligence" {
  name = var.meeting_topic_name
}

resource "aws_sqs_queue" "media_processing" {
  name = var.media_queue_name
}

resource "aws_sqs_queue" "transcription" {
  name = var.transcription_queue
}

resource "aws_sqs_queue" "enrichment" {
  name = var.enrichment_queue
}

resource "aws_sqs_queue" "task_creation" {
  name = var.task_queue
}

resource "aws_sqs_queue" "notifications" {
  name = var.notification_queue
}

