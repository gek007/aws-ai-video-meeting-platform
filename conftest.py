from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYTHON_SRC_DIRS = [
    ROOT / "apps" / "api" / "src",
    ROOT / "services" / "ingestion-service" / "src",
    ROOT / "services" / "media-service" / "src",
    ROOT / "services" / "transcription-service" / "src",
    ROOT / "services" / "ai-enrichment-service" / "src",
    ROOT / "services" / "task-orchestrator-service" / "src",
    ROOT / "services" / "integration-service" / "src",
    ROOT / "services" / "notification-service" / "src",
    ROOT / "services" / "status-observer-service" / "src",
    ROOT / "services" / "search-query-service" / "src",
    ROOT / "services" / "chat-rag-service" / "src",
    ROOT / "libs" / "contracts" / "src",
    ROOT / "libs" / "shared" / "src",
    ROOT / "libs" / "observability" / "src",
    ROOT / "libs" / "connectors" / "src",
]

for src_dir in PYTHON_SRC_DIRS:
    src = str(src_dir)
    if src not in sys.path:
        sys.path.insert(0, src)
