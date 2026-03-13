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


def _xpr_strict_eq(a: Any, b: Any) -> bool:
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return a == b


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
    if method == "indexOf":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'indexOf': expected 1, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], str):
            raise XprError("Type error: indexOf expects string argument", pos)
        return float(s.find(args[0]))
    if method == "repeat":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'repeat': expected 1, got {len(args)}",
                pos,
            )
        n = args[0]
        if (
            isinstance(n, bool)
            or not isinstance(n, (int, float))
            or not float(n).is_integer()
            or float(n) < 0
        ):
            raise XprError("Type error: repeat expects non-negative integer", pos)
        return s * int(n)
    if method == "trimStart":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'trimStart': expected 0, got {len(args)}",
                pos,
            )
        return s.lstrip()
    if method == "trimEnd":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'trimEnd': expected 0, got {len(args)}",
                pos,
            )
        return s.rstrip()
    if method == "charAt":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'charAt': expected 1, got {len(args)}",
                pos,
            )
        if isinstance(args[0], bool) or not isinstance(args[0], (int, float)):
            raise XprError("Type error: charAt expects number argument", pos)
        idx = int(args[0])
        if idx < 0 or idx >= len(s):
            return ""
        return s[idx]
    if method == "padStart":
        if len(args) < 1 or len(args) > 2:
            raise XprError(
                f"Wrong number of arguments for 'padStart': expected 1-2, got {len(args)}",
                pos,
            )
        if isinstance(args[0], bool) or not isinstance(args[0], (int, float)):
            raise XprError("Type error: padStart expects number argument", pos)
        n = int(args[0])
        pad_char = args[1] if len(args) == 2 else " "
        if not isinstance(pad_char, str):
            raise XprError("Type error: padStart pad character must be string", pos)
        fill = pad_char[0] if pad_char else " "
        return s.rjust(n, fill)
    if method == "padEnd":
        if len(args) < 1 or len(args) > 2:
            raise XprError(
                f"Wrong number of arguments for 'padEnd': expected 1-2, got {len(args)}",
                pos,
            )
        if isinstance(args[0], bool) or not isinstance(args[0], (int, float)):
            raise XprError("Type error: padEnd expects number argument", pos)
        n = int(args[0])
        pad_char = args[1] if len(args) == 2 else " "
        if not isinstance(pad_char, str):
            raise XprError("Type error: padEnd pad character must be string", pos)
        fill = pad_char[0] if pad_char else " "
        return s.ljust(n, fill)

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
    if method == "includes":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'includes': expected 1, got {len(args)}",
                pos,
            )
        target = args[0]
        for el in arr:
            if _xpr_strict_eq(el, target):
                return True
        return False
    if method == "indexOf":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'indexOf': expected 1, got {len(args)}",
                pos,
            )
        target = args[0]
        for i, el in enumerate(arr):
            if _xpr_strict_eq(el, target):
                return float(i)
        return float(-1)
    if method == "slice":
        if len(args) < 1 or len(args) > 2:
            raise XprError(
                f"Wrong number of arguments for 'slice': expected 1-2, got {len(args)}",
                pos,
            )
        if isinstance(args[0], bool) or not isinstance(args[0], (int, float)):
            raise XprError("Type error: slice expects number argument", pos)
        start = int(args[0])
        if len(args) == 2:
            if isinstance(args[1], bool) or not isinstance(args[1], (int, float)):
                raise XprError("Type error: slice expects number argument", pos)
            return arr[start : int(args[1])]
        return arr[start:]
    if method == "join":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'join': expected 1, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], str):
            raise XprError("Type error: join expects string argument", pos)

        def to_str(v):
            if v is None:
                return "null"
            if isinstance(v, bool):
                return "true" if v else "false"
            if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
                return str(int(v))
            return str(v)

        return args[0].join(to_str(el) for el in arr)
    if method == "concat":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'concat': expected 1, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], list):
            raise XprError("Type error: concat expects array argument", pos)
        return arr + args[0]
    if method == "flat":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'flat': expected 0, got {len(args)}",
                pos,
            )
        result = []
        for el in arr:
            if isinstance(el, list):
                result.extend(el)
            else:
                result.append(el)
        return result
    if method == "unique":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'unique': expected 0, got {len(args)}",
                pos,
            )
        seen = []
        result = []
        for el in arr:
            found = False
            for s in seen:
                if _xpr_strict_eq(el, s):
                    found = True
                    break
            if not found:
                seen.append(el)
                result.append(el)
        return result
    if method == "zip":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'zip': expected 1, got {len(args)}", pos
            )
        if not isinstance(args[0], list):
            raise XprError("Type error: zip expects array argument", pos)
        other = args[0]
        length = min(len(arr), len(other))
        return [[arr[i], other[i]] for i in range(length)]
    if method == "chunk":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'chunk': expected 1, got {len(args)}",
                pos,
            )
        n = args[0]
        if (
            isinstance(n, bool)
            or not isinstance(n, (int, float))
            or not float(n).is_integer()
            or float(n) <= 0
        ):
            raise XprError("Type error: chunk size must be a positive integer", pos)
        size = int(n)
        return [arr[i : i + size] for i in range(0, len(arr), size)]
    if method == "groupBy":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'groupBy': expected 1 function, got {len(args)}",
                pos,
            )
        groups: dict = {}
        for el in arr:
            key = str(args[0](el))
            if key not in groups:
                groups[key] = []
            groups[key].append(el)
        return {k: groups[k] for k in sorted(groups.keys())}

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
    if method == "entries":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'entries': expected 0, got {len(args)}",
                pos,
            )
        return [[k, obj[k]] for k in sorted(obj.keys())]
    if method == "has":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'has': expected 1, got {len(args)}", pos
            )
        if not isinstance(args[0], str):
            raise XprError("Type error: has expects string argument", pos)
        return args[0] in obj

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

    def _range(*args):
        if len(args) == 1:
            raw_start, raw_end, raw_step = 0, args[0], 1
        elif len(args) == 2:
            raw_start, raw_end, raw_step = args[0], args[1], 1
        elif len(args) == 3:
            raw_start, raw_end, raw_step = args[0], args[1], args[2]
        else:
            raise XprError(
                f"Wrong number of arguments for 'range': expected 1-3, got {len(args)}"
            )
        for orig in (raw_start, raw_end, raw_step):
            if isinstance(orig, bool) or not isinstance(orig, (int, float)):
                raise XprError("Type error: range expects number arguments")
        start, end, step = float(raw_start), float(raw_end), float(raw_step)
        if not step.is_integer():
            raise XprError("Type error: range step must be an integer, got float")
        if step == 0:
            raise XprError("Type error: range step cannot be zero")
        step_int = int(step)
        result = []
        if step_int > 0:
            i = start
            while i < end:
                result.append(i)
                i += step_int
        else:
            i = start
            while i > end:
                result.append(i)
                i += step_int
        return result

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
        "range": _range,
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
