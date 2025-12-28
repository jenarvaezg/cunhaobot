# cunhaobot

## Project Overview

**cunhaobot** is a multi-platform chatbot designed to reply with "brother-in-law-like" (cuñao) phrases. It integrates with **Telegram**, **Slack**, and **Twitter**, and is hosted on **Google Cloud App Engine**.

The core application is written in **Python**, utilizing **Litestar** to handle webhooks.

## Tech Stack

*   **Runtime:** Python 3.14 (Google App Engine Standard Environment)
*   **Web Framework:** Litestar
*   **Database:** Google Cloud Datastore (NoSQL)
*   **Bot APIs:**
    *   `python-telegram-bot` (Telegram)
    *   Slack API (Webhooks & Interactivity)
    *   `tweepy` (Twitter)
*   **Toolchain:**
    *   `uv`: Dependency management and script execution.
    *   `ruff`: Fast linting and formatting.
    *   `ty`: Astral's fast type checker (replacing mypy).
    *   `uvicorn`: ASGI server for running the Litestar app.
*   **Cloud Services:**
    *   Google App Engine (Hosting)
    *   Google Cloud Datastore (Persistence)

    ## Project Structure
    *   `main.py`: The entry point for the Litestar application. It defines routes for Telegram and Slack webhooks and health checks.
*   `tg/`: Contains logic specific to the Telegram bot.
    *   `handlers/`: Command and message handlers (e.g., `start.py`, `text_message.py`).
    *   `text_router.py`: Logic for routing incoming text messages.
*   `slack/`: Contains logic specific to the Slack bot.
*   `models/`: Python classes representing data entities (e.g., `phrase.py`, `user.py`), likely wrapping Datastore interaction.
*   `utils/`: General utilities, such as GCP connection helpers (`gcp.py`).
*   `scripts/`: Utility scripts (e.g., for sticker management).

## Setup & Development

### Prerequisites
*   Python 3.14+
*   Google Cloud SDK (`gcloud` CLI)

### Environment Variables
The application relies heavily on environment variables for configuration and secrets. Refer to `app.yaml.example` for the required keys:
*   `TG_TOKEN`: Telegram Bot Token
*   `SLACK_CLIENT_ID` / `SLACK_CLIENT_SECRET`: Slack App credentials
*   `TWITTER_*`: Twitter API credentials
*   `MOD_CHAT_ID`: ID for a moderation chat
*   `OWNER_ID`: Bot owner's ID

### Python (Main App)

1.  **Install Dependencies:**
    Using [uv](https://github.com/astral-sh/uv):
    ```bash
    uv sync
    ```

    To generate `requirements.txt` for deployment:
    ```bash
    uv export --no-hashes --format requirements-txt > requirements.txt
    ```

2.  **Linting & Type Checking:**
    ```bash
    uv run ruff check .
    uv run ty check
    ```

3.  **Run Locally:**
    Ensure you have set the necessary environment variables (see above).
    ```bash
    uv run main.py
    ```
    *Note: The local server runs on port 5050 by default.*

## Agent Guidelines

This project uses custom agent "skills" and patterns to ensure code quality and consistency. Before working on the codebase, agents MUST consult:

*   `.gemini/skills/README.md`: Index of guidelines and patterns.
*   `.gemini/skills/SKILL.md`: Core Python 3.14+ philosophy.
*   `.gemini/skills/PATTERNS.md`: Idiomatic coding patterns.
*   `.gemini/skills/TESTING.md`: Guidelines and patterns for testing.

### HTMX Integration
The project uses the specialized Litestar HTMX plugin for web interactivity.
*   **Request Class**: Use `litestar.plugins.htmx.HTMXRequest` to handle incoming web requests. This provides properties like `request.htmx` to detect HTMX-driven requests.
*   **Response Class**: Use `litestar.plugins.htmx.HTMXTemplate` for returning template responses, especially when dealing with partial updates or fragments.
*   **Configuration**: The `Litestar` application must be configured with `request_class=HTMXRequest` and a proper `TemplateConfig`.

### Git Workflow
*   **NEVER** use the `--no-verify` flag when making a commit. All commits must pass the pre-commit hooks.
*   **ALWAYS** run the full test suite (`uv run pytest src/`) and ensure all tests pass before making a commit.

### Python Coding Standards
*   **NEVER** use `# type: ignore` without specifying the specific error code (e.g., `# type: ignore[invalid-argument-type]`).

## CI/CD & Deployment

### Automated Deployment
The project uses GitHub Actions (`.github/workflows/deploy.yml`) for automated deployment.
*   **Parallel Verification:** Linting (`pre-commit`) and Testing (`pytest`) run in parallel.
*   **Deployment:** Only proceeds if both verification jobs pass.

### Manual Deployment
The project includes a shell script for deploying to Google App Engine and cleaning up previous versions. Ensure `requirements.txt` is up to date before deploying.

```bash
./deploy.sh
```

**Manual Command:**
```bash
gcloud app deploy
```

## Key Files

*   `main.py`: Main Litestar server file.
*   `.gemini/skills/`: Custom agent instructions and coding patterns.
*   `app.yaml.example`: Template for App Engine configuration and environment variables.
*   `deploy.sh`: Automated deployment script.
*   `pyproject.toml`: Project configuration, dependencies, and `ty` configuration.
*   `requirements.txt`: Frozen dependencies for App Engine deployment.
