import pytest

DUMMY_MAIN = """
import os, sys
sys.exit(int(os.environ.get("DUMMY_EXIT_CODE", "0")))
"""


@pytest.fixture
def dummy_module(tmp_path):
    mod_dir = tmp_path / "dummy_mod"
    mod_dir.mkdir()
    (mod_dir / "main.py").write_text(DUMMY_MAIN)
    return mod_dir
