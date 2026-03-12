import pytest
from xpr import Xpr


def test_not_implemented():
    engine = Xpr()
    with pytest.raises(NotImplementedError):
        engine.evaluate("1 + 2")
