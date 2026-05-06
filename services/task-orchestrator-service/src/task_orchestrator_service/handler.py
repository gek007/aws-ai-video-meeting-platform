from __future__ import annotations

from shared.responses import json_response
from task_orchestrator_service.service import TaskOrchestratorService


def lambda_handler(event: dict, _context) -> dict:
    result = TaskOrchestratorService().orchestrate(event)
    return json_response(202, {"message": "Task creation request prepared.", "nextEvent": result})

