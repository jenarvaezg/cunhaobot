# Tech Stack: cunhaobot

## Core Runtime
*   **Language:** Python 3.14+
*   **Dependency Management:** [uv](https://github.com/astral-sh/uv)

## Frameworks & Libraries
*   **Web Framework:** [Litestar](https://litestar.dev/) (ASGI)
*   **Bot Frameworks:**
    *   `python-telegram-bot` (Telegram)
    *   `slack-bolt` / `slack-sdk` (Slack)
    *   `tweepy` (Twitter/X)
*   **AI & Logic:**
    *   `pydantic-ai` (Agentic logic)
    *   `pydantic` v2 (Data validation and settings)
    *   `google-genai` (Gemini integration)
*   **Utilities:**
    *   `jinja2` (Templating)
    *   `pillow` (Image processing)
    *   `google-cloud-texttospeech` (TTS)

## Infrastructure & Persistence
*   **Cloud Platform:** Google Cloud Platform (GCP)
*   **Hosting:** Google App Engine (Standard Environment)
*   **Database:** Google Cloud Datastore (NoSQL)
*   **Storage:** Google Cloud Storage
*   **Observability:** `logfire`

## Development & Quality Assurance
*   **Linter/Formatter:** `ruff`
*   **Type Checker:** `ty` (Astral's fast type checker)
*   **Test Framework:** `pytest` (with `pytest-asyncio` and `pytest-cov`)
*   **Pre-commit Hooks:** `pre-commit` configuration for automated checks.
