import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from state.auth_state import auth_state


@pytest.fixture(autouse=True)
def _clean_session():
    auth_state.clear()
    yield
    auth_state.clear()
