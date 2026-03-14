from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union, List, Any, Optional


@dataclass
class NumberLiteral:
    value: float
    position: int


@dataclass
class StringLiteral:
    value: str
    position: int


@dataclass
class BooleanLiteral:
    value: bool
    position: int


@dataclass
class NullLiteral:
    position: int


@dataclass
class Property:
    key: str
    value: Any  # Expression
    position: int


@dataclass
class SpreadProperty:
    argument: Any  # Expression
    position: int


@dataclass
class ArrayExpression:
    elements: List[Any]  # List[Expression]
    position: int


@dataclass
class ObjectExpression:
    properties: List[Any]  # List[Union[Property, SpreadProperty]]
    position: int


@dataclass
class Identifier:
    name: str
    position: int


@dataclass
class MemberExpression:
    object: Any  # Expression
    property: Any  # str or Expression
    computed: bool
    optional: bool
    position: int


@dataclass
class BinaryExpression:
    op: str  # +, -, *, /, %, **, ==, !=, <, >, <=, >=
    left: Any
    right: Any
    position: int


@dataclass
class LogicalExpression:
    op: str  # &&, ||, ??
    left: Any
    right: Any
    position: int


@dataclass
class UnaryExpression:
    op: str  # !, -
    argument: Any
    position: int


@dataclass
class ConditionalExpression:
    test: Any
    consequent: Any
    alternate: Any
    position: int


@dataclass
class ArrowFunction:
    params: List[Any]  # List[str | ObjectPattern | ArrayPattern]
    body: Any
    position: int


@dataclass
class CallExpression:
    callee: Any
    arguments: List[Any]
    optional: bool
    position: int


@dataclass
class TemplateLiteral:
    quasis: List[str]
    expressions: List[Any]
    position: int


@dataclass
class PipeExpression:
    left: Any
    right: Any
    position: int


@dataclass
class SpreadElement:
    argument: Any
    position: int


@dataclass
class RegexLiteral:
    pattern: str
    flags: str
    position: int


@dataclass
class PatternProperty:
    key: str
    value: Any  # BindingTarget (str | ObjectPattern | ArrayPattern)
    default_value: Any  # Expression | None
    shorthand: bool
    rest: bool
    position: int


@dataclass
class ArrayPatternElement:
    element: Any  # BindingTarget
    default_value: Any  # Expression | None
    rest: bool
    position: int


@dataclass
class ObjectPattern:
    properties: List[Any]  # List[PatternProperty]
    position: int


@dataclass
class ArrayPattern:
    elements: List[Any]  # List[ArrayPatternElement]
    position: int


@dataclass
class LetExpression:
    name: Any  # str | ObjectPattern | ArrayPattern
    value: Any  # Expression
    body: Any  # Expression
    position: int


Expression = Union[
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    NullLiteral,
    ArrayExpression,
    ObjectExpression,
    Identifier,
    MemberExpression,
    BinaryExpression,
    LogicalExpression,
    UnaryExpression,
    ConditionalExpression,
    ArrowFunction,
    CallExpression,
    TemplateLiteral,
    PipeExpression,
    SpreadElement,
    SpreadProperty,
    LetExpression,
    RegexLiteral,
]
