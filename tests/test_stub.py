from xpr import Xpr


def test_basic_arithmetic():
    engine = Xpr()
    assert engine.evaluate("1 + 2") == 3


def test_custom_function():
    engine = Xpr()
    engine.add_function("double", lambda x: x * 2)
    assert engine.evaluate("double(5)") == 10
