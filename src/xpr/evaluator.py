from __future__ import annotations
import time
from typing import Any, Dict, Callable
from .errors import XprError
from .types import (
    Expression,
    NumberLiteral,
    StringLiteral,
    BooleanLiteral,
    NullLiteral,
    ArrayExpression,
    ObjectExpression,
    Property,
    SpreadProperty,
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
    LetExpression,
    RegexLiteral,
    ObjectPattern,
    ArrayPattern,
)
from .functions import (
    xpr_type,
    is_truthy,
    call_string_method,
    call_array_method,
    call_object_method,
    call_regex_method,
    is_regex,
    GLOBAL_FUNCTIONS,
    GLOBAL_FUNCTION_ARITY,
    GLOBAL_CONSTANTS,
)


def _expand_args(raw_args, nxt):
    result = []
    for arg in raw_args:
        if isinstance(arg, SpreadElement):
            val = nxt(arg.argument)
            if val is None:
                raise XprError("Cannot spread null", arg.position)
            if not isinstance(val, list):
                raise XprError("Cannot spread non-array", arg.position)
            result.extend(val)
        else:
            result.append(nxt(arg))
    return result


def _destructure_into(target, value, ctx, nxt):
    if isinstance(target, str):
        ctx[target] = value
        return
    if isinstance(target, ObjectPattern):
        if value is None:
            raise XprError("Cannot destructure null")
        obj = value if isinstance(value, dict) else {}
        used_keys = set()
        for prop in target.properties:
            if prop.rest:
                rest = {k: v for k, v in obj.items() if k not in used_keys}
                ctx[prop.value] = rest
            else:
                used_keys.add(prop.key)
                val = obj.get(prop.key, None)
                if val is None and prop.default_value is not None:
                    val = nxt(prop.default_value)
                _destructure_into(prop.value, val, ctx, nxt)
    elif isinstance(target, ArrayPattern):
        if value is None:
            raise XprError("Cannot destructure null")
        if not isinstance(value, list):
            raise XprError("Cannot destructure non-array as array")
        arr = value
        i = 0
        for el in target.elements:
            if el.rest:
                ctx[el.element] = arr[i:]
                break
            val = arr[i] if i < len(arr) else None
            if val is None and el.default_value is not None:
                val = nxt(el.default_value)
            _destructure_into(el.element, val, ctx, nxt)
            i += 1


BLOCKED_PROPS = frozenset(
    [
        "__proto__",
        "constructor",
        "prototype",
        "__defineGetter__",
        "__defineSetter__",
        "__lookupGetter__",
        "__lookupSetter__",
    ]
)
MAX_DEPTH = 50
TIMEOUT_MS = 100


def _dispatch_method_or_error(obj: Any, method: str, args: list, pos: int) -> Any:
    if isinstance(obj, str):
        return call_string_method(obj, method, args, pos)
    if isinstance(obj, list):
        return call_array_method(obj, method, args, pos)
    if isinstance(obj, dict):
        return call_object_method(obj, method, args, pos)
    raise XprError(f"Pipe RHS '{method}' is not callable on {xpr_type(obj)}", pos)


def eval_expr(
    node: Expression,
    ctx: Dict[str, Any],
    fns: Dict[str, Callable],
    depth: int = 0,
    start_time: float = None,
) -> Any:
    if start_time is None:
        start_time = time.time()

    if depth > MAX_DEPTH:
        raise XprError("Expression depth limit exceeded", getattr(node, "position", -1))
    if (time.time() - start_time) * 1000 > TIMEOUT_MS:
        raise XprError("Expression timeout exceeded")

    def nxt(n: Expression) -> Any:
        return eval_expr(n, ctx, fns, depth + 1, start_time)

    if isinstance(node, NumberLiteral):
        return node.value

    if isinstance(node, StringLiteral):
        return node.value

    if isinstance(node, BooleanLiteral):
        return node.value

    if isinstance(node, NullLiteral):
        return None

    if isinstance(node, ArrayExpression):
        result = []
        for el in node.elements:
            if isinstance(el, SpreadElement):
                val = nxt(el.argument)
                if val is None:
                    raise XprError("Cannot spread null", el.position)
                if isinstance(val, str):
                    raise XprError("Cannot spread string into array", el.position)
                if not isinstance(val, list):
                    raise XprError("Cannot spread non-array into array", el.position)
                result.extend(val)
            else:
                result.append(nxt(el))
        return result

    if isinstance(node, ObjectExpression):
        result = {}
        for prop in node.properties:
            if isinstance(prop, SpreadProperty):
                val = nxt(prop.argument)
                if val is None:
                    raise XprError("Cannot spread null", prop.position)
                if isinstance(val, list):
                    raise XprError("Cannot spread array into object", prop.position)
                if not isinstance(val, dict):
                    raise XprError("Cannot spread non-object", prop.position)
                result.update(val)
            else:
                result[prop.key] = nxt(prop.value)
        return result

    if isinstance(node, LetExpression):
        val = nxt(node.value)
        child_ctx = {**ctx}
        _destructure_into(node.name, val, child_ctx, nxt)
        return eval_expr(node.body, child_ctx, fns, depth + 1, start_time)

    if isinstance(node, RegexLiteral):
        import re as _re

        flags = 0
        if "i" in node.flags:
            flags |= _re.IGNORECASE
        if "m" in node.flags:
            flags |= _re.MULTILINE
        if "s" in node.flags:
            flags |= _re.DOTALL
        try:
            compiled = _re.compile(node.pattern, flags)
        except _re.error as e:
            raise XprError(f"invalid regex pattern: {e}", node.position)
        return {
            "__xpr_regex": True,
            "pattern": node.pattern,
            "flags": node.flags,
            "compiled": compiled,
        }

    if isinstance(node, Identifier):
        if node.name in ctx:
            return ctx[node.name]
        if node.name in GLOBAL_CONSTANTS:
            return GLOBAL_CONSTANTS[node.name]
        if node.name in GLOBAL_FUNCTIONS:
            return GLOBAL_FUNCTIONS[node.name]
        if node.name in fns:
            return fns[node.name]
        raise XprError(f"Unknown identifier '{node.name}'", node.position)

    if isinstance(node, MemberExpression):
        obj = nxt(node.object)
        if node.optional and obj is None:
            return None
        if obj is None:
            raise XprError("Cannot access property on null", node.position)

        if node.computed:
            key = nxt(node.property)
            if isinstance(key, (int, float)) and not isinstance(key, bool):
                idx = int(key)
                if not isinstance(obj, list):
                    raise XprError("Cannot index non-array with number", node.position)
                if idx < 0:
                    idx = len(obj) + idx
                return obj[idx] if 0 <= idx < len(obj) else None
            prop_name = str(key)
        else:
            prop_name = node.property

        if prop_name in BLOCKED_PROPS:
            raise XprError(
                f"Access denied: '{prop_name}' is a restricted property", node.position
            )

        if prop_name == "length" and isinstance(obj, list):
            return len(obj)

        if isinstance(obj, dict):
            return obj.get(prop_name, None)

        return None

    if isinstance(node, BinaryExpression):
        left = nxt(node.left)
        right = nxt(node.right)
        op = node.op

        if op == "==":
            if is_regex(left) and is_regex(right):
                return (
                    left["pattern"] == right["pattern"]
                    and left["flags"] == right["flags"]
                )
            if isinstance(left, bool) != isinstance(right, bool):
                return False
            return left == right
        if op == "!=":
            if is_regex(left) and is_regex(right):
                return (
                    left["pattern"] != right["pattern"]
                    or left["flags"] != right["flags"]
                )
            if isinstance(left, bool) != isinstance(right, bool):
                return True
            return left != right

        if is_regex(left) or is_regex(right):
            raise XprError(
                f"Type error: cannot use operator '{op}' with regex", node.position
            )

        if op == "+":
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if (
                isinstance(left, (int, float))
                and not isinstance(left, bool)
                and isinstance(right, (int, float))
                and not isinstance(right, bool)
            ):
                return left + right
            raise XprError(
                f"Type error: cannot add {xpr_type(left)} and {xpr_type(right)}",
                node.position,
            )

        if op in ("<", ">", "<=", ">="):
            if (
                isinstance(left, (int, float))
                and not isinstance(left, bool)
                and isinstance(right, (int, float))
                and not isinstance(right, bool)
            ):
                if op == "<":
                    return left < right
                if op == ">":
                    return left > right
                if op == "<=":
                    return left <= right
                return left >= right
            if isinstance(left, str) and isinstance(right, str):
                if op == "<":
                    return left < right
                if op == ">":
                    return left > right
                if op == "<=":
                    return left <= right
                return left >= right
            raise XprError(
                f"Type error: cannot compare {xpr_type(left)} and {xpr_type(right)}",
                node.position,
            )

        # Remaining ops require numbers
        if not (isinstance(left, (int, float)) and not isinstance(left, bool)) or not (
            isinstance(right, (int, float)) and not isinstance(right, bool)
        ):
            raise XprError(
                f"Type error: operator '{op}' requires numbers, got {xpr_type(left)} and {xpr_type(right)}",
                node.position,
            )
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise XprError("Division by zero", node.position)
            return left / right
        if op == "%":
            if right == 0:
                raise XprError("Division by zero", node.position)
            return left % right
        if op == "**":
            return left**right
        raise XprError(f"Unknown operator '{op}'", node.position)

    if isinstance(node, LogicalExpression):
        left = nxt(node.left)
        if node.op == "&&":
            return nxt(node.right) if is_truthy(left) else left
        if node.op == "||":
            return left if is_truthy(left) else nxt(node.right)
        if node.op == "??":
            return left if left is not None else nxt(node.right)
        raise XprError(f"Unknown logical operator '{node.op}'", node.position)

    if isinstance(node, UnaryExpression):
        arg = nxt(node.argument)
        if node.op == "!":
            return not is_truthy(arg)
        if node.op == "-":
            if not (isinstance(arg, (int, float)) and not isinstance(arg, bool)):
                raise XprError(
                    f"Type error: unary minus requires number, got {xpr_type(arg)}",
                    node.position,
                )
            return -arg
        raise XprError(f"Unknown unary operator '{node.op}'", node.position)

    if isinstance(node, ConditionalExpression):
        test = nxt(node.test)
        return nxt(node.consequent) if is_truthy(test) else nxt(node.alternate)

    if isinstance(node, ArrowFunction):
        params = node.params
        body = node.body
        rest_param = node.rest_param
        captured_ctx = dict(ctx)

        def arrow(*args):
            child_ctx = dict(captured_ctx)
            for i, p in enumerate(params):
                arg = args[i] if i < len(args) else None
                if isinstance(p, str):
                    child_ctx[p] = arg
                else:
                    inner_nxt = lambda e, _ctx=child_ctx: eval_expr(
                        e, _ctx, fns, depth + 1, start_time
                    )
                    _destructure_into(p, arg, child_ctx, inner_nxt)
            if rest_param:
                child_ctx[rest_param] = list(args[len(params) :])
            return eval_expr(body, child_ctx, fns, depth + 1, start_time)

        return arrow

    if isinstance(node, CallExpression):
        pos = node.position

        if isinstance(node.callee, MemberExpression):
            member = node.callee
            obj = nxt(member.object)

            if member.optional and obj is None:
                return None

            if member.computed:
                method_name = str(nxt(member.property))
            else:
                method_name = member.property

            if method_name in BLOCKED_PROPS:
                raise XprError(
                    f"Access denied: '{method_name}' is a restricted property", pos
                )

            args = _expand_args(node.arguments, nxt)

            if isinstance(obj, str):
                return call_string_method(obj, method_name, args, pos)
            if isinstance(obj, list):
                return call_array_method(obj, method_name, args, pos)
            if is_regex(obj):
                return call_regex_method(obj, method_name, args, pos)
            if isinstance(obj, dict):
                return call_object_method(obj, method_name, args, pos)

            raise XprError(
                f"Type error: cannot call method '{method_name}' on {xpr_type(obj)}",
                pos,
            )

        if isinstance(node.callee, Identifier):
            name = node.callee.name
            args = _expand_args(node.arguments, nxt)
            if name in ctx and callable(ctx[name]):
                return ctx[name](*args)
            if name in GLOBAL_FUNCTIONS:
                arity = GLOBAL_FUNCTION_ARITY.get(name)
                if arity is not None and len(args) != arity:
                    raise XprError(
                        f"Wrong number of arguments for '{name}': expected {arity}, got {len(args)}",
                        pos,
                    )
                return GLOBAL_FUNCTIONS[name](*args)
            if name in fns:
                return fns[name](*args)
            raise XprError(f"Unknown function '{name}'", pos)

        callee = nxt(node.callee)
        if node.optional and callee is None:
            return None
        args = _expand_args(node.arguments, nxt)
        if callable(callee):
            return callee(*args)
        raise XprError("Cannot call non-function", pos)

    if isinstance(node, PipeExpression):
        left = nxt(node.left)
        right = node.right

        if isinstance(right, CallExpression):
            extra_args = [nxt(a) for a in right.arguments]
            if isinstance(right.callee, Identifier):
                name = right.callee.name
                if name in GLOBAL_FUNCTIONS:
                    arity = GLOBAL_FUNCTION_ARITY.get(name)
                    if arity is not None and len(extra_args) + 1 != arity:
                        raise XprError(
                            f"Wrong number of arguments for '{name}'", node.position
                        )
                    return GLOBAL_FUNCTIONS[name](left, *extra_args)
                if name in fns:
                    return fns[name](left, *extra_args)
                return _dispatch_method_or_error(left, name, extra_args, node.position)
            callee = nxt(right.callee)
            if not callable(callee):
                raise XprError("Pipe RHS must be callable", node.position)
            return callee(left, *extra_args)

        if isinstance(right, Identifier):
            name = right.name
            if name in GLOBAL_FUNCTIONS:
                return GLOBAL_FUNCTIONS[name](left)
            if name in fns:
                return fns[name](left)
            return _dispatch_method_or_error(left, name, [], node.position)

        rhs_val = nxt(node.right)
        if callable(rhs_val):
            return rhs_val(left)
        raise XprError("Pipe RHS must be callable", node.position)

    if isinstance(node, TemplateLiteral):
        result = node.quasis[0]
        for i, expr in enumerate(node.expressions):
            val = nxt(expr)
            if val is None:
                s = "null"
            elif isinstance(val, bool):
                s = "true" if val else "false"
            elif isinstance(val, float) and val == int(val) and abs(val) < 1e15:
                s = str(int(val))
            else:
                s = str(val)
            result += s
            result += node.quasis[i + 1] if i + 1 < len(node.quasis) else ""
        return result

    if isinstance(node, SpreadElement):
        raise XprError("SpreadElement used outside array context", node.position)

    raise XprError(f"Unknown AST node type: {type(node).__name__}")
