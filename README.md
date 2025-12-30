# cunhaobot
Small Telegram bot that returns brother-in-law-like phrases like ¿Que pasa, maquina?

Puedes consultar el archivo de la sabiduría cuñadil en [https://20251228t205520-dot-cunhaobot.nw.r.appspot.com/](https://20251228t205520-dot-cunhaobot.nw.r.appspot.com/)

<a href="https://slack.com/oauth/v2/authorize?client_id=3215397142246.3245811070480&scope=chat:write,chat:write.public,commands,chat:write.customize,files:write&user_scope="><img alt="Add to Slack" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcSet="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>

## Desarrollo Local

Para probar el bot en local sin depender de GCP:

1.  **Configura el entorno:** Copia el archivo de ejemplo y rellena tus tokens:
    ```bash
    cp .env.example .env
    ```
2.  **Arranca el emulador y la app:** El script `dev.sh` se encarga de levantar el emulador de Datastore mediante Docker y arrancar el servidor Litestar:
    ```bash
    ./dev.sh
    ```

### Requisitos
- Docker y Docker Compose
- [uv](https://github.com/astral-sh/uv)
- Python 3.14
