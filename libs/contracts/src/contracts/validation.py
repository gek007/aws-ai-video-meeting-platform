from __future__ import annotations


class ContractValidationError(ValueError):
    pass


def require_keys(payload: dict, required: list[str]) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise ContractValidationError(f"Missing required keys: {', '.join(missing)}")

