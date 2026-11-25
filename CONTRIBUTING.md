# Contributing to rql-python

Contributions, bug reports, and feature requests are welcome!

## Development Setup

```bash
git clone https://github.com/altunga/rql-python.git
cd rql-python
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .\.venv\Scripts\activate
pip install -e ".[sqlalchemy,dev]"
```

## Running Checks

Before opening a pull request, make sure all tests, strict type checks, and samples pass:

```bash
pytest -v
mypy --strict src tests samples
python -m samples.main
```

## Pull Request Guidelines

- Add unit or integration tests for new features and bug fixes.
- Keep all code strictly typed (`mypy --strict` clean).
- Keep the core `src/rql` package domain-agnostic with zero required third-party dependencies.
