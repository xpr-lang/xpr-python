from __future__ import annotations
import json
import math
from typing import Any, Callable, List
from .errors import XprError


def xpr_type(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    if callable(v):
        return "function"
    return "unknown"


def is_truthy(v: Any) -> bool:
    if v is False or v is None or v == 0 or v == "":
        return False
    return True


def call_string_method(obj: Any, method: str, args: List[Any], pos: int) -> Any:
    if not isinstance(obj, str):
        raise XprError(
            f"Type error: cannot call method '{method}' on {xpr_type(obj)}", pos
        )
    s = obj

    if method == "len":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'len': expected 0, got {len(args)}", pos
            )
        return len(s)
    if method == "upper":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'upper': expected 0, got {len(args)}",
                pos,
            )
        return s.upper()
    if method == "lower":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'lower': expected 0, got {len(args)}",
                pos,
            )
        return s.lower()
    if method == "trim":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'trim': expected 0, got {len(args)}",
                pos,
            )
        return s.strip()
    if method == "startsWith":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'startsWith': expected 1, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], str):
            raise XprError("Type error: startsWith expects string argument", pos)
        return s.startswith(args[0])
    if method == "endsWith":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'endsWith': expected 1, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], str):
            raise XprError("Type error: endsWith expects string argument", pos)
        return s.endswith(args[0])
    if method == "contains":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'contains': expected 1, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], str):
            raise XprError("Type error: contains expects string argument", pos)
        return args[0] in s
    if method == "split":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'split': expected 1, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], str):
            raise XprError("Type error: split expects string argument", pos)
        return s.split(args[0])
    if method == "replace":
        if len(args) != 2:
            raise XprError(
                f"Wrong number of arguments for 'replace': expected 2, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], str) or not isinstance(args[1], str):
            raise XprError("Type error: replace expects string arguments", pos)
        return s.replace(args[0], args[1])
    if method == "slice":
        if len(args) < 1 or len(args) > 2:
            raise XprError(
                f"Wrong number of arguments for 'slice': expected 1-2, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], (int, float)):
            raise XprError("Type error: slice expects number argument", pos)
        start = int(args[0])
        if len(args) == 2:
            if not isinstance(args[1], (int, float)):
                raise XprError("Type error: slice expects number argument", pos)
            return s[start : int(args[1])]
        return s[start:]

    raise XprError(f"Type error: cannot call method '{method}' on string", pos)


def call_array_method(obj: Any, method: str, args: List[Any], pos: int) -> Any:
    if not isinstance(obj, list):
        raise XprError(
            f"Type error: cannot call method '{method}' on {xpr_type(obj)}", pos
        )
    arr = obj

    if method == "map":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'map': expected 1 function, got {len(args)}",
                pos,
            )
        return [args[0](el) for el in arr]
    if method == "filter":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'filter': expected 1 function, got {len(args)}",
                pos,
            )
        return [el for el in arr if is_truthy(args[0](el))]
    if method == "reduce":
        if len(args) != 2 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'reduce': expected 2 args (fn, init), got {len(args)}",
                pos,
            )
        acc = args[1]
        for el in arr:
            acc = args[0](acc, el)
        return acc
    if method == "find":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'find': expected 1 function, got {len(args)}",
                pos,
            )
        for el in arr:
            if is_truthy(args[0](el)):
                return el
        return None
    if method == "some":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'some': expected 1 function, got {len(args)}",
                pos,
            )
        return any(is_truthy(args[0](el)) for el in arr)
    if method == "every":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'every': expected 1 function, got {len(args)}",
                pos,
            )
        return all(is_truthy(args[0](el)) for el in arr)
    if method == "flatMap":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'flatMap': expected 1 function, got {len(args)}",
                pos,
            )
        result = []
        for el in arr:
            r = args[0](el)
            if isinstance(r, list):
                result.extend(r)
            else:
                result.append(r)
        return result
    if method == "sort":
        if len(args) > 1:
            raise XprError(
                f"Wrong number of arguments for 'sort': expected 0-1, got {len(args)}",
                pos,
            )
        copy = list(arr)
        if not args or args[0] is None:

            def default_key(x):
                if isinstance(x, (int, float)) and not isinstance(x, bool):
                    return (0, x, "")
                return (1, 0, str(x))

            copy.sort(key=default_key)
        else:
            if not callable(args[0]):
                raise XprError("Type error: sort expects function argument", pos)
            import functools

            def cmp(a, b):
                r = args[0](a, b)
                return int(r) if isinstance(r, (int, float)) else 0

            copy.sort(key=functools.cmp_to_key(cmp))
        return copy
    if method == "reverse":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'reverse': expected 0, got {len(args)}",
                pos,
            )
        return list(reversed(arr))

    raise XprError(f"Type error: cannot call method '{method}' on array", pos)


def call_object_method(obj: Any, method: str, args: List[Any], pos: int) -> Any:
    if not isinstance(obj, dict):
        raise XprError(
            f"Type error: cannot call method '{method}' on {xpr_type(obj)}", pos
        )

    if method == "keys":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'keys': expected 0, got {len(args)}",
                pos,
            )
        return list(obj.keys())
    if method == "values":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'values': expected 0, got {len(args)}",
                pos,
            )
        return list(obj.values())

    raise XprError(f"Type error: cannot call method '{method}' on object", pos)


def _make_global_functions() -> dict:
    def _round(n):
        if not isinstance(n, (int, float)) or isinstance(n, bool):
            raise XprError("Type error: round expects number")
        return round(float(n))

    def _floor(n):
        if not isinstance(n, (int, float)) or isinstance(n, bool):
            raise XprError("Type error: floor expects number")
        return math.floor(float(n))

    def _ceil(n):
        if not isinstance(n, (int, float)) or isinstance(n, bool):
            raise XprError("Type error: ceil expects number")
        return math.ceil(float(n))

    def _abs(n):
        if not isinstance(n, (int, float)) or isinstance(n, bool):
            raise XprError("Type error: abs expects number")
        return abs(float(n))

    def _min(a, b):
        if (
            not isinstance(a, (int, float))
            or isinstance(a, bool)
            or not isinstance(b, (int, float))
            or isinstance(b, bool)
        ):
            raise XprError("Type error: min expects numbers")
        return min(float(a), float(b))

    def _max(a, b):
        if (
            not isinstance(a, (int, float))
            or isinstance(a, bool)
            or not isinstance(b, (int, float))
            or isinstance(b, bool)
        ):
            raise XprError("Type error: max expects numbers")
        return max(float(a), float(b))

    def _type(v):
        return xpr_type(v)

    def _int(v):
        if isinstance(v, bool):
            raise XprError(f"Type error: cannot convert {xpr_type(v)} to int")
        if isinstance(v, (int, float)):
            return int(math.trunc(float(v)))
        if isinstance(v, str):
            try:
                return int(math.trunc(float(v)))
            except ValueError:
                raise XprError(f'Type error: cannot convert "{v}" to int')
        raise XprError(f"Type error: cannot convert {xpr_type(v)} to int")

    def _float(v):
        if isinstance(v, bool):
            raise XprError(f"Type error: cannot convert {xpr_type(v)} to float")
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise XprError(f'Type error: cannot convert "{v}" to float')
        raise XprError(f"Type error: cannot convert {xpr_type(v)} to float")

    def _string(v):
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return (
                str(v)
                if not isinstance(v, float) or v != int(v)
                else str(int(v))
                if abs(v) < 1e15
                else str(v)
            )
        if isinstance(v, str):
            return v
        return json.dumps(v)

    def _bool(v):
        return is_truthy(v)

    return {
        "round": _round,
        "floor": _floor,
        "ceil": _ceil,
        "abs": _abs,
        "min": _min,
        "max": _max,
        "type": _type,
        "int": _int,
        "float": _float,
        "string": _string,
        "bool": _bool,
    }


GLOBAL_FUNCTIONS = _make_global_functions()
GLOBAL_FUNCTION_ARITY = {
    "round": 1,
    "floor": 1,
    "ceil": 1,
    "abs": 1,
    "min": 2,
    "max": 2,
    "type": 1,
    "int": 1,
    "float": 1,
    "string": 1,
    "bool": 1,
}
