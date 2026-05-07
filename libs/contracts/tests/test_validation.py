import pytest

from contracts.validation import ContractValidationError, require_keys


def test_require_keys_accepts_complete_payload():
    require_keys({"a": 1, "b": 2}, ["a", "b"])


def test_require_keys_raises_for_missing_keys():
    with pytest.raises(ContractValidationError):
        require_keys({"a": 1}, ["a", "b"])
