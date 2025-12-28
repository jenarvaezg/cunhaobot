# cunhaobot

## Project Overview

**cunhaobot** is a multi-platform chatbot designed to reply with "brother-in-law-like" (cuñao) phrases. It integrates with **Telegram**, **Slack**, and **Twitter**, and is hosted on **Google Cloud App Engine**.

The core application is written in **Python**, utilizing **Flask** to handle webhooks.

## Tech Stack

*   **Runtime:** Python 3.14 (Google App Engine Standard Environment)
*   **Web Framework:** Flask
*   **Database:** Google Cloud Datastore (NoSQL)
*   **Bot APIs:**
    *   `python-telegram-bot` (Telegram)
    *   Slack API (Webhooks & Interactivity)
    *   `tweepy` (Twitter)
*   **Cloud Services:**
    *   Google App Engine (Hosting)
    *   Google Cloud Datastore (Persistence)
    *   AWS S3 (Implied by `boto3` dependency, likely for media storage)

## Project Structure

*   `main.py`: The entry point for the Flask application. It defines routes for Telegram and Slack webhooks and health checks.
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
*   `AWS_*`: AWS credentials
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

2.  **Run Locally:**
    Ensure you have set the necessary environment variables (see above).
    ```bash
    uv run main.py
    ```
    *Note: The local server runs on port 5050 by default.*

## Deployment

The project includes a shell script for deploying to Google App Engine and cleaning up previous versions.

Ensure `requirements.txt` is up to date before deploying.

```bash
./deploy.sh
```

**Manual Deployment:**
```bash
gcloud app deploy
```

## Key Files

*   `main.py`: Main Flask server file.
*   `app.yaml.example`: Template for App Engine configuration and environment variables.
*   `deploy.sh`: Automated deployment script.
*   `pyproject.toml`: Project configuration and dependencies (managed by uv).
*   `requirements.txt`: Frozen dependencies for App Engine deployment.
