# Cunhaobot Architecture Documentation

This document outlines the architecture of the Cunhaobot project, focusing on its Clean Architecture implementation, use of Pydantic v2, Protocol-based repositories, and Dependency Injection.

## 1. Layers and Responsibilities

The project is structured into distinct layers, each with specific responsibilities:

*   **`api/` (Controllers)**:
    *   **Responsibility**: Handles incoming requests (HTTP, webhooks), parses input, and orchestrates the flow by calling services.
    *   **Characteristics**: Controllers are kept lean, focusing on request/response handling and dependency injection. They should not contain business logic.
    *   **Framework**: Litestar is used for handling web requests.
    *   **Examples**: `src/api/admin.py` (Admin web interface), `src/api/slack.py` (Slack webhook handler), `src/api/bot.py` (Telegram and Twitter handlers).

*   **`services/` (Application/Business Logic)**:
    *   **Responsibility**: Contains the core business logic and use cases of the application. It orchestrates domain entities and interacts with repositories.
    *   **Characteristics**: Services are independent of external frameworks and delivery mechanisms. They define *what* the application does.
    *   **Examples**: `src/services/phrase_service.py`, `src/services/proposal_service.py`, `src/services/user_service.py`.

*   **`models/` (Domain Entities)**:
    *   **Responsibility**: Defines the core data structures and domain rules of the application.
    *   **Characteristics**: Pure Python classes representing the business concepts. They should **NOT** contain persistence logic (e.g., `save()`, `load()` methods).
    *   **Framework**: [Pydantic v2](https://docs.pydantic.dev/latest/) is used for defining data models, providing data validation and serialization.
    *   **Modern Typing**: Uses Python 3.14+ features strictly (`| None` instead of `Optional`, `list[T]` instead of `List`).
    *   **Examples**: `src/models/phrase.py`, `src/models/user.py`, `src/models/proposal.py`, `src/services/badge_service.py` (contains `Badge` and `BadgeProgress`).

*   **`infrastructure/` (Data Access & External Interfaces)**:
    *   **Responsibility**: Implements the details of how data is stored and retrieved, and how external services (e.g., Telegram API, Slack API, Google Cloud Datastore) are accessed.
    *   **Characteristics**: This layer depends on the `protocols/` layer (abstractions) and specific external technologies. It contains the concrete implementations of the repository interfaces.
    *   **Sub-layers**:
        *   **`protocols/`**: Defines abstract interfaces (Python `Protocol` classes) for repositories, ensuring dependency inversion. Services depend on these abstractions, not concrete implementations. **Avoid `Any` in protocols**; use concrete types or generic bounds.
        *   **`datastore/`**: Contains the concrete implementations of repositories using Google Cloud Datastore.
    *   **Examples**: `src/infrastructure/protocols.py`, `src/infrastructure/datastore/phrase.py` (implements `PhraseRepository`).

*   **`core/` (Configuration)**:
    *   **Responsibility**: Manages application-wide configuration settings and environment variables.
    *   **Characteristics**: Centralized access to configuration, ensuring consistency.
    *   **Example**: `src/core/config.py`.

*   **`utils/` (Cross-cutting Concerns)**:
    *   **Responsibility**: Provides general utility functions that are reused across different layers but do not belong to any specific domain logic.
    *   **Characteristics**: Helper functions that can be used by any layer without introducing strong coupling.
    *   **Examples**: `src/utils/gcp.py`, `src/utils/text.py`.

## 2. Key Architectural Principles

### 2.1. Clean Architecture

The project adheres to the principles of Clean Architecture, emphasizing separation of concerns and testability.
*   **Independence of Frameworks**: The core business logic (services and models) is independent of external frameworks (Litestar, Google Cloud).
*   **Testability**: Each layer can be tested in isolation, with external dependencies easily mocked.
*   **Dependency Rule**: Dependencies always flow inwards. The outer layers depend on inner layers, but inner layers have no knowledge of outer layers.
    *   `api` depends on `services`
    *   `services` depends on `models` and `infrastructure/protocols`
    *   `infrastructure/datastore` depends on `models` and implements `infrastructure/protocols`

### 2.2. Pydantic v2 for Domain Models

All domain entities (e.g., `Phrase`, `User`, `Proposal`) are implemented using [Pydantic v2](https://docs.pydantic.dev/latest/). This provides:
*   **Data Validation**: Automatic validation of data types and constraints.
*   **Serialization/Deserialization**: Easy conversion to/from JSON or other formats.
*   **Immutability (Optional)**: Can define models as immutable if desired.
*   **Clearer Data Schemas**: Explicitly defines the structure and types of data.

**Important**: Pydantic models in the `models/` layer should be pure data structures and **should NOT contain persistence logic** (e.g., `save()`, `load()` methods). Persistence is handled by the `infrastructure/datastore` layer via repositories.

### 2.3. Protocol-based Repositories

The `infrastructure/protocols.py` module defines abstract interfaces (Python `Protocol` classes) for all repositories (e.g., `PhraseRepository`, `UserRepository`).

*   **Dependency Inversion**: Services depend on these abstract `Protocol` definitions, not on the concrete `Datastore*Repository` implementations. This means that if the underlying database changes (e.g., from Datastore to PostgreSQL), only the `infrastructure/datastore` implementations need to be updated; the `services` layer remains untouched.
*   **Testability**: Mocking repositories for unit testing services becomes straightforward by providing mock objects that adhere to the `Protocol` interface.

### 2.4. Dependency Injection (DI)

[Litestar's Dependency Injection system](https://litestar.dev/usage/dependency-injection.html) is used to provide dependencies (services, repositories) to controllers.

*   **Mechanism**: Dependencies are declared using `Annotated[Any, Dependency()]` in controller method signatures.
*   **Configuration**: Instances of services and repositories are registered in `src/main.py` using `Provide()`. This centralizes the wiring of dependencies.
*   **Testability**: During testing, concrete implementations can be easily swapped out for mock implementations, further enhancing isolation and testability.

## 3. Technology Stack

*   **Runtime**: Python 3.14 (Google App Engine Standard Environment)
*   **Web Framework**: Litestar
*   **Database**: Google Cloud Datastore (NoSQL)
*   **Pydantic**: Data validation and serialization
*   **Telegram Bot API**: `python-telegram-bot`
*   **Slack API**: Webhooks & Interactivity
*   **Twitter API**: `tweepy`
*   **Cloud Services**: Google App Engine, Google Cloud Datastore

## 4. Project Structure (High-level)

```
.
├── src/
│   ├── api/                # HTTP/Webhook Handlers (Controllers)
│   ├── core/               # Configuration
│   ├── infrastructure/
│   │   ├── datastore/      # Concrete Repository Implementations (e.g., DatastorePhraseRepository)
│   │   └── protocols.py    # Abstract Repository Interfaces (e.g., PhraseRepository Protocol)
│   ├── models/             # Domain Entities (Pydantic models)
│   ├── services/           # Business Logic (e.g., PhraseService)
│   ├── slack/              # Slack-specific handlers/utils
│   ├── tg/                 # Telegram-specific handlers/utils
│   └── utils/              # General utilities
├── main.py                 # Litestar App setup, DI container
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # General project information
└── ARCHITECTURE.md         # This document
```
