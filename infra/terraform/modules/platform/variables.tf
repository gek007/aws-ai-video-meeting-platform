variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "raw_video_bucket" {
  type = string
}

variable "audio_bucket" {
  type = string
}

variable "transcript_bucket" {
  type = string
}

variable "artifacts_bucket" {
  type = string
}

variable "meeting_topic_name" {
  type = string
}

variable "media_queue_name" {
  type = string
}

variable "transcription_queue" {
  type = string
}

variable "enrichment_queue" {
  type = string
}

variable "task_queue" {
  type = string
}

variable "notification_queue" {
  type = string
}
