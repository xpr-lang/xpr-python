class Xpr:
    def evaluate(self, expression: str, context: dict | None = None) -> object:
        raise NotImplementedError("XPR Python runtime not yet implemented")

    def add_function(self, name: str, fn) -> None:
        raise NotImplementedError("XPR Python runtime not yet implemented")
