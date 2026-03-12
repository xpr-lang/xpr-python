from .errors import XprError
from .tokenizer import tokenize
from .parser import parse
from .evaluator import eval_expr

__all__ = ["Xpr", "XprError"]


class Xpr:
    def __init__(self):
        self._functions = {}

    def evaluate(self, expression: str, context: dict | None = None) -> object:
        if context is None:
            context = {}
        tokens = tokenize(expression)
        ast = parse(tokens)
        return eval_expr(ast, context, self._functions)

    def add_function(self, name: str, fn) -> None:
        self._functions[name] = fn
