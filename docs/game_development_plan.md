# Plan de Desarrollo: Paco's Tapas Runner

Este plan detalla los pasos técnicos para implementar el juego HTML5 en la infraestructura actual de `cunhaobot`.

## Fase 1: Setup en Telegram (Bot Side) ✅
*   **Registro del juego:** Usar `@BotFather` para crear el juego (`palillo_cunhao`). (Completado ✅)
*   **Handler de Juego:** Implementar en `src/tg/handlers/commands/game.py` el comando `/jugar`. (Completado ✅)
*   **Callback Query:** Configurar el bot para responder a `callback_query` de tipo juego. (Completado ✅)

## Fase 2: Backend (Litestar API) ✅
*   **Endpoint de Lanzamiento:** Ruta GET `/game/launch` que valide al usuario y devuelva el HTML del juego. (Completado ✅)
*   **Endpoint de Puntuación:** Ruta POST `/api/game/score`. (Completado ✅)
*   **Validación de Integridad:** Implementado hash SHA-256. (Completado ✅)
*   **Integración con Puntos:** Suma de puntos en Datastore activa. (Completado ✅)

## Fase 3: Frontend (El Juego HTML5) 🚧
*   **Framework:** Phaser.js. (Esqueleto funcional listo ✅)
*   **Estructura:**
    *   `src/templates/game.html`: Contenedor principal y lógica del juego.
*   **Mejoras en desarrollo:**
    *   Implementar sistema de vidas (servilletas).
    *   Añadir assets reales (tapas, obstáculos).
    *   Implementar Power-up (Carajillo).

## Fase 4: Integración Social (Leaderboards) 🚧
*   **Telegram API:** Usar `setGameScore` para actualizar el ranking nativo. (Funcional ✅)
*   **Visualización:** El mensaje original mostrará automáticamente el Top 3. (Funcional ✅)

## Fase 5: Pulido y Lanzamiento
*   **Assets IA:** Generar los sprites finales.
*   **Beta Test:** Probar en el grupo de moderación.
*   **Anuncio:** Broadcast a todos los usuarios.
