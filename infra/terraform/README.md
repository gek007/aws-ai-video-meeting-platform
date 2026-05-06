# Terraform Layout

This directory contains the Terraform baseline for the platform.

- `bootstrap`
  State bootstrap and shared prerequisites.
- `environments/dev`
  Environment-specific entrypoint for development.
- `modules/platform`
  Reusable module that provisions the core AWS platform resources.

