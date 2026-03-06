# CLAUDE.md

## Project Overview

bookcrypt is a Python 3 project.

## Tech Stack

- **Language**: Python 3.12+
- **Testing**: pytest
- **Linting**: ruff
- **Formatting**: ruff format
- **Type checking**: mypy
- **Docs**: Google-style docstrings

## Project Structure

```
bookcrypt/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── bookcrypt/
│   ├── __init__.py
│   └── ...
└── tests/
    ├── __init__.py
    └── ...
```

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=bookcrypt --cov-report=term-missing

# Lint
ruff check .

# Format
ruff format .

# Type check
mypy bookcrypt/
```

## Code Conventions

- Follow PEP 8
- Use type hints on all public functions and methods
- Write Google-style docstrings for all public APIs
- Keep functions small and focused
- Prefer explicit over implicit

## Testing Conventions

- One test file per source module: `tests/test_<module>.py`
- Use `pytest` fixtures for shared setup
- Name tests descriptively: `test_<function>_<scenario>_<expected>`
- Aim for high coverage on core logic; don't test implementation details
- Unit tests should not make network calls or write to disk unless explicitly testing I/O

## Documentation

- All public functions, classes, and modules must have docstrings
- README.md should stay up to date with setup and usage instructions
- Use inline comments only where the logic is non-obvious

## Git

- Commit messages: imperative mood, lowercase, no period (e.g. `add encryption module`)
- Do not commit secrets, credentials, or large binary files
- Keep commits focused and atomic
