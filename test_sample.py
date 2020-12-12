import main
import pytest

assert main.main(0) == pytest.approx(21.425e6,abs=1e4)