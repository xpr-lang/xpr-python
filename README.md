# xpr-python — XPR Expression Language for Python

[![CI](https://github.com/xpr-lang/xpr-python/actions/workflows/ci.yml/badge.svg)](https://github.com/xpr-lang/xpr-python/actions)
[![Status: Coming Soon](https://img.shields.io/badge/status-coming%20soon-orange)](https://github.com/xpr-lang/xpr-python)

> 🚧 **Coming Soon** — Python runtime for the XPR expression language.

## About

XPR is a sandboxed cross-language expression language for data pipeline transforms. This repo will contain the Python runtime.

See the [XPR Language Specification](https://github.com/xpr-lang/xpr) for the full grammar and conformance test suite.

## Planned API

```python
from xpr import Xpr

engine = Xpr()
result = engine.evaluate(
    "items.filter(x => x.price > threshold).map(x => x.name)",
    context={"items": [...], "threshold": 50}
)
```

## Contributing

This runtime is not yet implemented. Contributions welcome — see the spec repo for the language definition and conformance tests.
