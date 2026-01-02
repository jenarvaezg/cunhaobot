# cunhaobot
Small Telegram bot that returns brother-in-law-like phrases like ¿Que pasa, maquina?

Puedes consultar el archivo de la sabiduría cuñadil en [https://cunhaobot.nw.r.appspot.com/](https://cunhaobot.nw.r.appspot.com/)

<a href="https://cunhaobot.nw.r.appspot.com/slack/auth"><img alt="Add to Slack" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcSet="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>

## Características y Comandos

El bot es una parodia afectuosa del típico "cuñado" español. Ofrece:

*   **IA Conversacional:** Menciona al bot o háblale por privado y te responderá sentando cátedra sobre cualquier tema.
*   **Gestión de Comunidad:** Sistema de puntos, ranking y medallas.

### Comandos Principales

*   `/cuñao [texto]`: Devuelve una frase aleatoria o filtrada.
*   `/sticker [texto]`: Envía un sticker.
*   `/saludo [nombre]`: Genera un saludo personalizado (ej: "¿Qué pasa, fiera?").
*   `/proponer [texto]`: Propone nuevas frases para el repertorio.
*   `/perfil`: Muestra tus estadísticas y medallas.

### Fusión de Cuentas (/link)

Si usas el bot en varias plataformas (Telegram y Slack), puedes unificar tu perfil:

1.  En la cuenta que quieras **abandonar** (origen), escribe `/link`. El bot te dará un código.
2.  En tu cuenta **principal** (destino), escribe `/link <CODIGO>`.
3.  Tus puntos y medallas se transferirán a la cuenta principal y la de origen se borrará.

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
