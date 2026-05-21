import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


FIXTURES_DIR = Path(__file__).parent / "fixtures"
