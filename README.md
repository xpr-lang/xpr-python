# xpr-python — XPR Expression Language for Python

[![CI](https://github.com/xpr-lang/xpr-python/actions/workflows/ci.yml/badge.svg)](https://github.com/xpr-lang/xpr-python/actions)
[![PyPI](https://img.shields.io/pypi/v/xpr-lang)](https://pypi.org/project/xpr-lang/)
[![XPR spec](https://img.shields.io/badge/XPR_spec-v0.5-blue)](https://github.com/xpr-lang/xpr)
[![conformance](https://img.shields.io/badge/conformance-100%25-brightgreen)](https://github.com/xpr-lang/xpr/tree/main/conformance)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**XPR** is a sandboxed cross-language expression language for data pipeline transforms. This is the Python runtime.

## Install

```bash
pip install xpr-lang
```

Requires Python 3.10+.

## Quick Start

```python
from xpr import Xpr

engine = Xpr()

engine.evaluate('items.filter(x => x.price > 50).map(x => x.name)', {
    'items': [
        {'name': 'Widget', 'price': 25},
        {'name': 'Gadget', 'price': 75},
        {'name': 'Doohickey', 'price': 100},
    ]
})
# → ["Gadget", "Doohickey"]
```

## API

### `evaluate(expression, context=None)`

Evaluates an XPR expression against an optional context object.

```python
from xpr import Xpr

engine = Xpr()

engine.evaluate('1 + 2')                          # → 3
engine.evaluate('user.name', {'user': {'name': 'Alice'}})  # → "Alice"
engine.evaluate('items.length', {'items': [1, 2, 3]})      # → 3
```

Returns the result as `object`. Raises `XprError` on parse or evaluation errors.

### `add_function(name, fn)`

Register a custom function callable from expressions:

```python
from xpr import Xpr

engine = Xpr()

engine.add_function('double', lambda x: x * 2)
engine.add_function('greet', lambda name: f'Hello, {name}!')

engine.evaluate('double(21)')           # → 42
engine.evaluate('greet("World")')       # → "Hello, World!"
engine.evaluate('items.map(x => double(x))', {'items': [1, 2, 3]})  # → [2, 4, 6]
```

## Built-in Functions

**Math**: `round`, `floor`, `ceil`, `abs`, `min`, `max`

**Type**: `type`, `int`, `float`, `string`, `bool`

**String methods**: `.len()`, `.upper()`, `.lower()`, `.trim()`, `.startsWith()`, `.endsWith()`, `.contains()`, `.split()`, `.replace()`, `.slice()`, `.indexOf()`, `.repeat()`, `.trimStart()`, `.trimEnd()`, `.charAt()`, `.padStart()`, `.padEnd()`

**Array methods**: `.map()`, `.filter()`, `.reduce()`, `.find()`, `.some()`, `.every()`, `.flatMap()`, `.sort()`, `.reverse()`, `.length`, `.includes()`, `.indexOf()`, `.slice()`, `.join()`, `.concat()`, `.flat()`, `.unique()`, `.zip()`, `.chunk()`, `.groupBy()`

**Object methods**: `.keys()`, `.values()`, `.entries()`, `.has()`

**Utility**: `range()`

## v0.2 Features

**Let Bindings**: Immutable scoped bindings allow you to define and reuse values within expressions:

```python
engine.evaluate('let x = 1; let y = x + 1; y')  # → 2
engine.evaluate('let items = [1, 2, 3]; items.map(x => x * 2)', {})  # → [2, 4, 6]
```

**Spread Operator**: Spread syntax for arrays and objects enables composition and merging:

```python
engine.evaluate('[1, 2, ...[3, 4]]')  # → [1, 2, 3, 4]
engine.evaluate('{...{a: 1}, b: 2}')  # → {'a': 1, 'b': 2}
```

## v0.3 Features

### Date/Time

Dates are epoch milliseconds (UTC only). Numbers return as `float`.

```python
engine.evaluate('formatDate(now(), "yyyy-MM-dd")')
# → "2026-03-15"

engine.evaluate('dateDiff(parseDate("2024-01-01T00:00:00Z"), now(), "days")')
# → 439.0

engine.evaluate('dateAdd(parseDate("2024-01-31T00:00:00Z"), 1, "months")')
# → 1709337600000.0
```

### Regex

Function-based regex (RE2 flavor).

```python
engine.evaluate('matches("hello 42", "\\\\d+")')               # → True
engine.evaluate('match("order-123", "\\\\d+")')                 # → "123"
engine.evaluate('matchAll("a1b2c3", "\\\\d")')                  # → ["1", "2", "3"]
engine.evaluate('replacePattern("hello world", "o", "0")')      # → "hell0 w0rld"
```

### Negative Indexing and Spread in Calls

```python
engine.evaluate('[1,2,3][-1]')           # → 3.0 (last element)
engine.evaluate('max(...[1, 5, 3, 2])')  # → 5.0
```

## v0.4 Features

### Destructuring

```python
engine.evaluate('let {name, age} = user; name', {'user': {'name': 'Alice', 'age': 30}})
# → 'Alice'

engine.evaluate('users.map(({name, age}) => `${name}: ${age}`)',
  {'users': [{'name': 'Alice', 'age': 30}]})
# → ['Alice: 30']

engine.evaluate('let [head, ...tail] = items; tail', {'items': [1, 2, 3]})
# → [2.0, 3.0]
```

### Regex Literals

```python
engine.evaluate('/\\\\d+/.test("order-123")')      # → True
engine.evaluate('"2024-01-15".match(/\\\\d{4}/)')  # → "2024"
engine.evaluate('"hello world".replace(/o/, "0")')  # → "hell0 w0rld"
```

## v0.5 Features

### Math

```python
engine.evaluate('sqrt(16)')        # → 4.0
engine.evaluate('log(E)')          # → 1.0
engine.evaluate('PI * pow(5, 2)')  # → 78.53981633974483
engine.evaluate('sign(-7)')        # → -1.0
engine.evaluate('trunc(3.9)')      # → 3.0
```

### Type Predicates

```python
engine.evaluate('isNumber(42)')     # → True
engine.evaluate('isString("x")')    # → True
engine.evaluate('isObject([1,2])') # → False (arrays are "array" type)
engine.evaluate('isNull(null)')     # → True
```

### New Array Methods

```python
engine.evaluate('[3,null,1,null,5].compact().sortBy(x => x)')   # → [1.0, 3.0, 5.0]
engine.evaluate('[1,2,3,4,5].take(3)')                           # → [1.0, 2.0, 3.0]
engine.evaluate('[1,2,3,4].sum()')                               # → 10.0
engine.evaluate('[1,2,3,4].avg()')                               # → 2.5
engine.evaluate('[3,1,2].first()')                               # → 3.0
```

### Other

```python
engine.evaluate('fromEntries([["a", 1], ["b", 2]])')  # → {'a': 1.0, 'b': 2.0}
engine.evaluate('"a1b2c3".split(/\\\\d+/)')             # → ['a', 'b', 'c']
```

## Conformance

This runtime supports **Level 1–3** (all conformance levels):
- Level 1: Literals, arithmetic, comparison, logic, ternary, property access, function calls
- Level 2: Arrow functions, collection methods, string methods, template literals
- Level 3: Pipe operator (`|>`), optional chaining (`?.`), nullish coalescing (`??`)

**v0.2 additions**: Let bindings, spread operator, 20 new built-in methods (10 array, 7 string, 2 object, 1 global)
**v0.3 additions**: Date/time (12 fns), regex functions (4 fns), negative indexing, spread in calls
**v0.4 additions**: Destructuring (let + arrow params), regex literals, `regex` type
**v0.5 additions**: 6 math fns + PI/E, 6 type predicates, 13 new array methods, `fromEntries()`, rest params

Passes all conformance tests (Levels 1–3 plus v0.2–v0.5 features).

## Specification

See the [XPR Language Specification](https://github.com/xpr-lang/xpr) for the full EBNF grammar, type system, operator precedence, and conformance test suite.

## License

MIT
