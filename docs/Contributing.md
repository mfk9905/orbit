# Contributing to Orbit

Thank you for contributing to Orbit!

## Code Style & Standards

- **Python**: PEP 8 compliance.
- **Type Annotations**: All functions must include complete type hints.
- **Docstrings**: All modules, classes, and methods must have descriptive docstrings.
- **Architecture**: Always enforce single-responsibility and MVVM separation. UI classes must never contain direct business logic.

## Running Tests

```bash
PYTHONPATH=. pytest tests/
```
