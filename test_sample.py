import main
import pytest

def test_SHS_index_0():
    assert main.main(0) == pytest.approx(21.425e6,abs=1e4)
