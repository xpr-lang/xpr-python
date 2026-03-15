from __future__ import annotations
import json
import math
import re as _re
import calendar as _calendar
from datetime import (
    datetime as _datetime,
    timezone as _timezone,
    timedelta as _timedelta,
)
from typing import Any, Callable, List
from .errors import XprError


def is_regex(v: Any) -> bool:
    return isinstance(v, dict) and v.get("__xpr_regex") is True


def call_regex_method(re_val: Any, method: str, args: list, pos: int) -> Any:
    if method == "test":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'test': expected 1, got {len(args)}",
                pos,
            )
        if not isinstance(args[0], str):
            raise XprError("Type error: test expects string", pos)
        return bool(re_val["compiled"].search(args[0]))
    raise XprError(f"Type error: regex has no method '{method}'", pos)


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
    if is_regex(v):
        return "regex"
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
        if is_regex(args[0]):
            return _re.split(args[0]["compiled"], s)
        if not isinstance(args[0], str):
            raise XprError("Type error: split expects string or regex argument", pos)
        return s.split(args[0])
    if method == "replace":
        if len(args) != 2:
            raise XprError(
                f"Wrong number of arguments for 'replace': expected 2, got {len(args)}",
                pos,
            )
        if not isinstance(args[1], str):
            raise XprError("Type error: replace replacement must be string", pos)
        if is_regex(args[0]):
            re_val = args[0]
            py_repl = _re.sub(r"\$(\d+)", r"\\\1", args[1])
            return re_val["compiled"].sub(py_repl, s)
        if not isinstance(args[0], str):
            raise XprError(
                "Type error: replace expects string or regex as first argument", pos
            )
        return s.replace(args[0], args[1])
    if method == "match":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'match': expected 1, got {len(args)}",
                pos,
            )
        if not is_regex(args[0]):
            raise XprError("Type error: match expects regex argument", pos)
        m = args[0]["compiled"].search(s)
        return m.group(0) if m else None
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

    if method == "sortBy":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'sortBy': expected 1 function, got {len(args)}",
                pos,
            )
        fn = args[0]
        keys = [fn(el) for el in arr]
        if not keys:
            return []
        all_numbers = all(
            isinstance(k, (int, float)) and not isinstance(k, bool) for k in keys
        )
        all_strings = all(isinstance(k, str) for k in keys)
        if not all_numbers and not all_strings:
            raise XprError(
                "Type error: sortBy key function must return all numbers or all strings",
                pos,
            )
        paired = list(zip(keys, arr))
        paired.sort(key=lambda x: x[0])  # type: ignore[return-value]
        return [x[1] for x in paired]
    if method == "take":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'take': expected 1, got {len(args)}",
                pos,
            )
        n = args[0]
        if not isinstance(n, (int, float)) or isinstance(n, bool) or n != int(n):
            raise XprError("Type error: take expects integer argument", pos)
        n = int(n)
        return [] if n <= 0 else arr[:n]
    if method == "drop":
        if len(args) != 1:
            raise XprError(
                f"Wrong number of arguments for 'drop': expected 1, got {len(args)}",
                pos,
            )
        n = args[0]
        if not isinstance(n, (int, float)) or isinstance(n, bool) or n != int(n):
            raise XprError("Type error: drop expects integer argument", pos)
        n = int(n)
        return arr if n <= 0 else arr[n:]
    if method == "count":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'count': expected 1 function, got {len(args)}",
                pos,
            )
        return sum(1 for el in arr if is_truthy(args[0](el)))
    if method == "sum":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'sum': expected 0, got {len(args)}", pos
            )
        if not arr:
            return 0.0
        for el in arr:
            if not isinstance(el, (int, float)) or isinstance(el, bool):
                raise XprError(
                    f"Type error: sum expects all elements to be numbers, got {xpr_type(el)}",
                    pos,
                )
        return float(sum(el for el in arr))
    if method == "avg":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'avg': expected 0, got {len(args)}", pos
            )
        if not arr:
            raise XprError("Type error: cannot compute average of empty array", pos)
        for el in arr:
            if not isinstance(el, (int, float)) or isinstance(el, bool):
                raise XprError(
                    f"Type error: avg expects all elements to be numbers, got {xpr_type(el)}",
                    pos,
                )
        return float(sum(el for el in arr)) / len(arr)
    if method == "compact":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'compact': expected 0, got {len(args)}",
                pos,
            )
        return [el for el in arr if el is not None]
    if method == "partition":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'partition': expected 1 function, got {len(args)}",
                pos,
            )
        matches = [el for el in arr if is_truthy(args[0](el))]
        non_matches = [el for el in arr if not is_truthy(args[0](el))]
        return [matches, non_matches]
    if method == "keyBy":
        if len(args) != 1 or not callable(args[0]):
            raise XprError(
                f"Wrong number of arguments for 'keyBy': expected 1 function, got {len(args)}",
                pos,
            )
        result = {}
        for el in arr:
            result[str(args[0](el))] = el
        return {k: result[k] for k in sorted(result.keys())}
    if method == "min":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'min': expected 0, got {len(args)}", pos
            )
        if not arr:
            raise XprError("Type error: cannot compute min of empty array", pos)
        for el in arr:
            if not isinstance(el, (int, float)) or isinstance(el, bool):
                raise XprError(
                    f"Type error: min expects all elements to be numbers, got {xpr_type(el)}",
                    pos,
                )
        return float(min(float(el) for el in arr))
    if method == "max":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'max': expected 0, got {len(args)}", pos
            )
        if not arr:
            raise XprError("Type error: cannot compute max of empty array", pos)
        for el in arr:
            if not isinstance(el, (int, float)) or isinstance(el, bool):
                raise XprError(
                    f"Type error: max expects all elements to be numbers, got {xpr_type(el)}",
                    pos,
                )
        return float(max(float(el) for el in arr))
    if method == "first":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'first': expected 0, got {len(args)}",
                pos,
            )
        return arr[0] if arr else None
    if method == "last":
        if args:
            raise XprError(
                f"Wrong number of arguments for 'last': expected 0, got {len(args)}",
                pos,
            )
        return arr[-1] if arr else None

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
        if is_regex(v):
            return f"/{v['pattern']}/{v['flags']}"
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

    _VALID_UNITS = {
        "years",
        "months",
        "days",
        "hours",
        "minutes",
        "seconds",
        "milliseconds",
    }

    def _now():
        return float(_datetime.now(_timezone.utc).timestamp() * 1000)

    def _parse_date(*args):
        if len(args) < 1 or len(args) > 2:
            raise XprError(
                f"Wrong number of arguments for 'parseDate': expected 1-2, got {len(args)}"
            )
        str_val = args[0]
        if not isinstance(str_val, str):
            raise XprError("Type error: parseDate expects string")
        fmt = args[1] if len(args) == 2 else None
        if fmt is None:
            try:
                s = str_val.replace("Z", "+00:00")
                if "T" not in s and len(s) == 10:
                    s = s + "T00:00:00+00:00"
                dt = _datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=_timezone.utc)
                return float(dt.timestamp() * 1000)
            except (ValueError, TypeError):
                raise XprError(f'invalid date string: "{str_val}"')
        if not isinstance(fmt, str):
            raise XprError("Type error: parseDate format must be string")
        token_patterns = {
            "yyyy": r"(\d{4})",
            "MM": r"(\d{2})",
            "dd": r"(\d{2})",
            "HH": r"(\d{2})",
            "mm": r"(\d{2})",
            "ss": r"(\d{2})",
            "SSS": r"(\d{3})",
        }
        token_names = _re.findall(r"yyyy|MM|dd|HH|mm|ss|SSS", fmt)
        regex_str = _re.escape(fmt)
        for t in token_names:
            regex_str = regex_str.replace(_re.escape(t), token_patterns[t], 1)
        m = _re.fullmatch(regex_str, str_val)
        if not m:
            raise XprError(
                f'invalid date string: "{str_val}" does not match format "{fmt}"'
            )
        year, month, day, hour, minute, second, ms = 1970, 1, 1, 0, 0, 0, 0
        for i, t in enumerate(token_names):
            v = int(m.group(i + 1))
            if t == "yyyy":
                year = v
            elif t == "MM":
                month = v
            elif t == "dd":
                day = v
            elif t == "HH":
                hour = v
            elif t == "mm":
                minute = v
            elif t == "ss":
                second = v
            elif t == "SSS":
                ms = v
        dt = _datetime(
            year, month, day, hour, minute, second, ms * 1000, tzinfo=_timezone.utc
        )
        return float(dt.timestamp() * 1000)

    def _format_date(date_val, fmt):
        if isinstance(date_val, bool) or not isinstance(date_val, (int, float)):
            raise XprError("Type error: formatDate expects number (epoch ms)")
        if not isinstance(fmt, str):
            raise XprError("Type error: formatDate format must be string")
        dt = _datetime.fromtimestamp(float(date_val) / 1000, tz=_timezone.utc)
        result = fmt
        result = result.replace("yyyy", str(dt.year).zfill(4))
        result = result.replace("MM", str(dt.month).zfill(2))
        result = result.replace("dd", str(dt.day).zfill(2))
        result = result.replace("HH", str(dt.hour).zfill(2))
        result = result.replace("mm", str(dt.minute).zfill(2))
        result = result.replace("ss", str(dt.second).zfill(2))
        result = result.replace("SSS", str(dt.microsecond // 1000).zfill(3))
        return result

    def _assert_epoch(v, name):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise XprError(f"Type error: {name} expects number (epoch ms)")
        return _datetime.fromtimestamp(float(v) / 1000, tz=_timezone.utc)

    def _year(v):
        return float(_assert_epoch(v, "year").year)

    def _month(v):
        return float(_assert_epoch(v, "month").month)

    def _day(v):
        return float(_assert_epoch(v, "day").day)

    def _hour(v):
        return float(_assert_epoch(v, "hour").hour)

    def _minute(v):
        return float(_assert_epoch(v, "minute").minute)

    def _second(v):
        return float(_assert_epoch(v, "second").second)

    def _millisecond(v):
        return float(_assert_epoch(v, "millisecond").microsecond // 1000)

    def _date_add(date_val, amount, unit):
        if isinstance(date_val, bool) or not isinstance(date_val, (int, float)):
            raise XprError("Type error: dateAdd expects number (epoch ms)")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise XprError("Type error: dateAdd amount must be number")
        if not isinstance(unit, str):
            raise XprError("Type error: dateAdd unit must be string")
        if unit not in _VALID_UNITS:
            raise XprError(f'invalid unit "{unit}" for dateAdd')
        amt = int(amount)
        dt = _datetime.fromtimestamp(float(date_val) / 1000, tz=_timezone.utc)
        if unit == "years":
            dt = dt.replace(year=dt.year + amt)
        elif unit == "months":
            total = (dt.month - 1) + amt
            new_year = dt.year + total // 12
            new_month = total % 12 + 1
            max_day = _calendar.monthrange(new_year, new_month)[1]
            overflow = max(0, dt.day - max_day)
            dt = dt.replace(year=new_year, month=new_month, day=min(dt.day, max_day))
            if overflow:
                dt = dt + _timedelta(days=overflow)
        elif unit == "days":
            dt = dt + _timedelta(days=amt)
        elif unit == "hours":
            dt = dt + _timedelta(hours=amt)
        elif unit == "minutes":
            dt = dt + _timedelta(minutes=amt)
        elif unit == "seconds":
            dt = dt + _timedelta(seconds=amt)
        elif unit == "milliseconds":
            return float(date_val) + float(amt)
        return float(dt.timestamp() * 1000)

    def _date_diff(date1, date2, unit):
        if isinstance(date1, bool) or not isinstance(date1, (int, float)):
            raise XprError("Type error: dateDiff expects number (epoch ms)")
        if isinstance(date2, bool) or not isinstance(date2, (int, float)):
            raise XprError("Type error: dateDiff expects number (epoch ms)")
        if not isinstance(unit, str):
            raise XprError("Type error: dateDiff unit must be string")
        if unit not in _VALID_UNITS:
            raise XprError(f'invalid unit "{unit}" for dateDiff')
        diff_ms = float(date2) - float(date1)
        if unit == "milliseconds":
            return diff_ms
        if unit == "seconds":
            return float(int(diff_ms / 1000))
        if unit == "minutes":
            return float(int(diff_ms / 60000))
        if unit == "hours":
            return float(int(diff_ms / 3600000))
        if unit == "days":
            return float(int(diff_ms / 86400000))
        d1 = _datetime.fromtimestamp(float(date1) / 1000, tz=_timezone.utc)
        d2 = _datetime.fromtimestamp(float(date2) / 1000, tz=_timezone.utc)
        if unit == "months":
            return float((d2.year - d1.year) * 12 + (d2.month - d1.month))
        if unit == "years":
            return float(d2.year - d1.year)

    def _extract_inline_flags(pattern):
        m = _re.match(r"^\(\?([imsu]+)\)(.*)", pattern, _re.DOTALL)
        if m:
            return m.group(2), m.group(1)
        return pattern, ""

    def _matches(str_val, pattern):
        if not isinstance(str_val, str):
            raise XprError("Type error: matches expects string")
        if not isinstance(pattern, str):
            raise XprError("Type error: matches pattern must be string")
        try:
            src, flags_str = _extract_inline_flags(pattern)
            flags = 0
            if "i" in flags_str:
                flags |= _re.IGNORECASE
            if "m" in flags_str:
                flags |= _re.MULTILINE
            if "s" in flags_str:
                flags |= _re.DOTALL
            return bool(_re.search(src, str_val, flags))
        except _re.error as e:
            raise XprError(f"invalid regex pattern: {e}")

    def _match(str_val, pattern):
        if not isinstance(str_val, str):
            raise XprError("Type error: match expects string")
        if not isinstance(pattern, str):
            raise XprError("Type error: match pattern must be string")
        try:
            src, flags_str = _extract_inline_flags(pattern)
            flags = 0
            if "i" in flags_str:
                flags |= _re.IGNORECASE
            if "m" in flags_str:
                flags |= _re.MULTILINE
            if "s" in flags_str:
                flags |= _re.DOTALL
            m = _re.search(src, str_val, flags)
            return m.group(0) if m else None
        except _re.error as e:
            raise XprError(f"invalid regex pattern: {e}")

    def _match_all(str_val, pattern):
        if not isinstance(str_val, str):
            raise XprError("Type error: matchAll expects string")
        if not isinstance(pattern, str):
            raise XprError("Type error: matchAll pattern must be string")
        try:
            src, flags_str = _extract_inline_flags(pattern)
            flags = 0
            if "i" in flags_str:
                flags |= _re.IGNORECASE
            if "m" in flags_str:
                flags |= _re.MULTILINE
            if "s" in flags_str:
                flags |= _re.DOTALL
            return _re.findall(src, str_val, flags)
        except _re.error as e:
            raise XprError(f"invalid regex pattern: {e}")

    def _replace_pattern(str_val, pattern, replacement):
        if not isinstance(str_val, str):
            raise XprError("Type error: replacePattern expects string")
        if not isinstance(pattern, str):
            raise XprError("Type error: replacePattern pattern must be string")
        if not isinstance(replacement, str):
            raise XprError("Type error: replacePattern replacement must be string")
        try:
            src, flags_str = _extract_inline_flags(pattern)
            flags = 0
            if "i" in flags_str:
                flags |= _re.IGNORECASE
            if "m" in flags_str:
                flags |= _re.MULTILINE
            if "s" in flags_str:
                flags |= _re.DOTALL
            py_repl = _re.sub(r"\$(\d+)", r"\\\1", replacement)
            return _re.sub(src, py_repl, str_val, flags=flags)
        except _re.error as e:
            raise XprError(f"invalid regex pattern: {e}")

    def _min_variadic(*args):
        if len(args) < 2:
            raise XprError(
                f"Wrong number of arguments for 'min': expected at least 2, got {len(args)}"
            )
        for a in args:
            if isinstance(a, bool) or not isinstance(a, (int, float)):
                raise XprError("Type error: min expects numbers")
        return min(args)

    def _max_variadic(*args):
        if len(args) < 2:
            raise XprError(
                f"Wrong number of arguments for 'max': expected at least 2, got {len(args)}"
            )
        for a in args:
            if isinstance(a, bool) or not isinstance(a, (int, float)):
                raise XprError("Type error: max expects numbers")
        return max(args)

    return {
        "round": _round,
        "floor": _floor,
        "ceil": _ceil,
        "abs": _abs,
        "min": _min_variadic,
        "max": _max_variadic,
        "type": _type,
        "int": _int,
        "float": _float,
        "string": _string,
        "bool": _bool,
        "range": _range,
        "now": _now,
        "parseDate": _parse_date,
        "formatDate": _format_date,
        "year": _year,
        "month": _month,
        "day": _day,
        "hour": _hour,
        "minute": _minute,
        "second": _second,
        "millisecond": _millisecond,
        "dateAdd": _date_add,
        "dateDiff": _date_diff,
        "matches": _matches,
        "match": _match,
        "matchAll": _match_all,
        "replacePattern": _replace_pattern,
        "sqrt": _sqrt,
        "log": _log,
        "pow": _pow,
        "random": _random,
        "sign": _sign,
        "trunc": _trunc,
        "isNumber": _is_number,
        "isString": _is_string,
        "isArray": _is_array,
        "isNull": _is_null,
        "isObject": _is_object,
        "isRegex": _is_regex_pred,
        "fromEntries": _from_entries,
    }


def _sqrt(n):
    if not isinstance(n, (int, float)) or isinstance(n, bool):
        raise XprError("Type error: sqrt expects number")
    if float(n) < 0:
        raise XprError("Type error: cannot compute sqrt of negative number")
    return math.sqrt(float(n))


def _log(n):
    if not isinstance(n, (int, float)) or isinstance(n, bool):
        raise XprError("Type error: log expects number")
    if float(n) <= 0:
        raise XprError("Type error: cannot compute log of non-positive number")
    return math.log(float(n))


def _pow(x, y):
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        raise XprError("Type error: pow expects number")
    if not isinstance(y, (int, float)) or isinstance(y, bool):
        raise XprError("Type error: pow expects number")
    return math.pow(float(x), float(y))


def _random():
    import random as _random_mod

    return float(_random_mod.random())


def _sign(n):
    if not isinstance(n, (int, float)) or isinstance(n, bool):
        raise XprError("Type error: sign expects number")
    v = float(n)
    if v > 0:
        return 1.0
    if v < 0:
        return -1.0
    return 0.0


def _trunc(n):
    if not isinstance(n, (int, float)) or isinstance(n, bool):
        raise XprError("Type error: trunc expects number")
    return float(math.trunc(float(n)))


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_string(v):
    return isinstance(v, str)


def _is_array(v):
    return isinstance(v, list)


def _is_null(v):
    return v is None


def _is_object(v):
    return isinstance(v, dict) and not is_regex(v)


def _is_regex_pred(v):
    return is_regex(v)


def _from_entries(pairs):
    if not isinstance(pairs, list):
        raise XprError("Type error: fromEntries expects array")
    result = {}
    for pair in pairs:
        if not isinstance(pair, list) or len(pair) < 2:
            raise XprError(
                "Type error: fromEntries each element must be [key, value] pair"
            )
        raw_key = pair[0]
        if isinstance(raw_key, float) and raw_key == int(raw_key):
            key = str(int(raw_key))
        else:
            key = str(raw_key)
        result[key] = pair[1]
    return {k: result[k] for k in sorted(result.keys())}


GLOBAL_FUNCTIONS = _make_global_functions()
GLOBAL_FUNCTION_ARITY = {
    "round": 1,
    "floor": 1,
    "ceil": 1,
    "abs": 1,
    "type": 1,
    "int": 1,
    "float": 1,
    "string": 1,
    "bool": 1,
    "sqrt": 1,
    "log": 1,
    "sign": 1,
    "trunc": 1,
    "isNumber": 1,
    "isString": 1,
    "isArray": 1,
    "isNull": 1,
    "isObject": 1,
    "isRegex": 1,
    "fromEntries": 1,
    "pow": 2,
    "random": 0,
}

GLOBAL_CONSTANTS = {
    "PI": math.pi,
    "E": math.e,
}
