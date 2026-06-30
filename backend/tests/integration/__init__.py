"""Integration tests — require full service stack. Skipped in unit test runs."""
import pytest

# The test_client fixture in conftest.py is a placeholder (returns None).
# These tests are scaffolding only; skip until a real async client is wired up.
pytestmark = pytest.mark.skip(reason="integration scaffold: test_client fixture not yet implemented")
