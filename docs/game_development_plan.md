# Plan de Desarrollo: Paco's Tapas Runner

Este plan detalla los pasos técnicos para implementar el juego HTML5 en la infraestructura actual de `cunhaobot`.

## Fase 1: Setup en Telegram (Bot Side)
*   **Registro del juego:** Usar `@BotFather` para crear el juego (`palillo_ninja`). Obtener el `game_short_name`.
*   **Handler de Juego:** Implementar en `src/tg/handlers/commands/game.py` el comando `/jugar` que envíe el juego al chat.
*   **Callback Query:** Configurar el bot para responder a `callback_query` de tipo juego, redirigiendo al usuario a la URL del juego con los parámetros necesarios (`user_id`, `inline_message_id`).

## Fase 2: Backend (Litestar API)
*   **Endpoint de Lanzamiento:** Ruta GET `/game/launch` que valide al usuario y devuelva el HTML del juego.
*   **Endpoint de Puntuación:** Ruta POST `/api/game/score` para recibir y validar la puntuación final.
*   **Validación de Integridad:** Implementar un sistema básico de "hash" o "token" para evitar que los usuarios envíen puntuaciones falsas fácilmente.
*   **Integración con Puntos:** Al terminar la partida, sumar `score / 100` a los puntos del usuario en Datastore.

## Fase 3: Frontend (El Juego HTML5)
*   **Framework:** Phaser.js (ligero y potente para 2D).
*   **Estructura:**
    *   `src/static/game/index.html`: Punto de entrada.
    *   `src/static/game/js/`: Lógica del juego (escenas de Carga, Menú y Juego).
    *   `src/static/game/assets/`: Imágenes (pixel art) y sonidos.
*   **Responsive:** Asegurar que el juego se adapte a cualquier tamaño de pantalla de móvil (Telegram WebView).

## Fase 4: Integración Social (Leaderboards)
*   **Telegram API:** Usar `setGameScore` para actualizar el ranking nativo de Telegram.
*   **Visualización:** El mensaje original del juego en Telegram mostrará automáticamente el Top 3 del grupo.

## Fase 5: Pulido y Lanzamiento
*   **Assets IA:** Generar los sprites de las tapas y los obstáculos usando modelos de IA para mantener la estética.
*   **Beta Test:** Probar en el grupo de moderación/dueño del bar.
*   **Anuncio:** Broadcast a todos los usuarios informando del nuevo juego y el ranking semanal.
