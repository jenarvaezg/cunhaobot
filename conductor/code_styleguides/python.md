# Python Development Guidelines (cunhaobot)

> **Source of Truth:** This document consolidates the project's core skills and patterns defined in `.gemini/skills/`.

---

# 1. Core Philosophy (Python 3.14+)

1. **Stdlib and Mature Libraries First**
   - Always prefer Python stdlib solutions.
   - External deps only when stdlib insufficient.
   - Prefer `dataclasses` over `attrs`, `pathlib` over `os.path`.

2. **Type Hints Everywhere (No Any)**
   - Python 3.14 has lazy annotations by default.
   - Use `Protocol` for structural typing (duck typing).
   - Avoid `Any`—use concrete types or generics.
   - **NEVER** use `typing.Optional`. Use `Type | None` instead (e.g., `str | None`).

3. **Protocol Over ABC**
   - Use `Protocol` for implicit interface satisfaction.
   - Use `ABC` only when runtime `isinstance()` checks are strictly needed.
   - Protocols are more flexible and Pythonic.

4. **Flat Control Flow**
   - Use Guard clauses with early returns.
   - Use Pattern matching (`match`/`case`) to flatten conditionals.
   - Maximum 2 levels of nesting.

5. **Explicit Error Handling**
   - Use custom exception hierarchy for domain errors.
   - Raise early, handle at boundaries.
   - Use Python 3.10+ syntax: `except ValueError | TypeError:` (no parens).

---

# 2. Project Architecture & Patterns

## Structure
Follow a modular structure with clear separation of concerns:

- **`src/api/`**: Controllers and route handlers. Purely for handling HTTP/IO and delegating to services.
- **`src/services/`**: Business logic and use cases. Orchestrates models and infrastructure.
- **`src/models/`**: Domain entities and basic persistence logic (Data Classes/Pydantic).
- **`src/core/`**: Centralized configuration and core constants.
- **`src/infrastructure/`**: Low-level external integrations (e.g., Datastore, Storage).
- **`src/utils/`**: Atomic, stateless utility functions grouped by topic (text, security, ui).

## Dependency Injection (Protocol-Based)

```python
from typing import Protocol

# Protocol at consumer (like Go interfaces)
class UserStore(Protocol):
    def get(self, id: str) -> User | None: ...
    def save(self, user: User) -> None: ...

class UserService:
    def __init__(self, store: UserStore):
        self.store = store  # accepts any matching impl
```

## Flat Control Flow

### Guard Clauses
```python
# GOOD: guard clauses, early returns
def process(user: User | None) -> Result:
    if user is None:
        raise ValueError("user required")
    if not user.email:
        raise ValueError("email required")
    return do_work(user)
```

### Pattern Matching
```python
# Flatten complex conditionals with match
match event:
    case {"type": "click", "x": x, "y": y}:
        handle_click(x, y)
    case {"type": "key", "code": code}:
        handle_key(code)
    case _:
        raise ValueError(f"Unknown event: {event}")
```

## Configuration (Dataclasses)
```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    database_url: str
    port: int = 8080

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            database_url=os.environ["DATABASE_URL"],
            port=int(os.environ.get("PORT", 8080)),
        )
```

---

# 3. Testing Standards

## Framework: `pytest`

```bash
uv run pytest -v
uv run pytest --cov=src
```

## Guidelines
- **Mandatory Workflow**: ALWAYS run the full test suite (`uv run pytest`) and ensure all tests pass 100% before making a commit.
- **100% Coverage**: ALWAYS ensure the test coverage remains at 100%.
- **File Naming**: Tests must end in `_test.py`.
- **Async Tests**: Use `@pytest.mark.asyncio`.

## Example
```python
import pytest
from unittest.mock import Mock

def test_validate_email_empty():
    with pytest.raises(ValidationError, match="email required"):
        validate_email("")

@pytest.mark.asyncio
async def test_service_flow():
    mock_repo = Mock()
    service = UserService(mock_repo)
    # ...
```

---

# 4. Tooling

- **Dependency Management:** `uv`
- **Linting:** `ruff check --fix .`
- **Formatting:** `ruff format .`
- **Type Checking:** `ty` (or `mypy`)
