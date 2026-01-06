# Plan de Desarrollo: Paco's Tapas Runner

Este plan detalla los pasos para convertir el prototipo actual en un juego digno de ganar una Game Jam.

## Fase 1: Infraestructura Core ✅
*   **Registro del juego:** `palillo_cunhao` registrado en BotFather. ✅
*   **Bot Handler:** Comando `/jugar` y gestión de callbacks. ✅
*   **Backend:** API de puntuación con validación SHA-256 e integración con Datastore. ✅
*   **Web Integration:** Acceso desde `/game` para debug y juego libre. ✅

## Fase 2: El "Juice" y Pulido Visual ✅
*   **Sustitución de Assets:**
    *   Cambiar formas geométricas por **Pixel Art 8-bit**. ✅
    *   Corrección de transparencia y sombras en assets. ✅
*   **Animaciones y Feedback:**
    *   Animación de "Squash & Stretch" (inclinación) en el palillo. ✅
    *   Efecto de rotación/balanceo en las tapas al caer. ✅
    *   **Sistema de Partículas:** Migas, chispas y manchas verdes. ✅
    *   **UI Feedback:** Tween de escala en el score. ✅
    *   **Screen Flash/Vibrate:** Feedback visual y háptico al perder vida. ✅
*   **Pantalla de Inicio:** Instrucciones y botón de comenzar. ✅

## Fase 3: Audio y Narrativa de Bar 🚧
*   **Voces Dinámicas (TTS):**
    *   Saludo personalizado ("¿Qué pasa, fiera?") al iniciar. ✅
    *   Frase de cuñado aleatoria al perder (Game Over). ✅
*   **Música de Fondo:**
    *   Bucle de Pasodoble estilo 8-bit/Chiptune (MP3/OGG). **(Falta Asset)**
*   **Efectos de Sonido (SFX):** **(Faltan Assets)**
    *   `crunch.mp3`: Al capturar croqueta/jamón.
    *   `damage.mp3`: Al chocar con aguacate/sushi.
    *   `powerup.mp3`: Al coger carajillo.
    *   `cash.mp3`: Al coger factura.

## Fase 4: Mecánicas Avanzadas (Dificultad y Variedad) 🎮
*   **Sistema de Combos:** Multiplicador de puntos si capturas 3 croquetas seguidas sin fallar.
*   **Patrones de Lluvia:** En lugar de caída aleatoria, crear "oleadas" (ej. una fila de aguacates con un solo hueco).
*   **Nuevos Elementos:**
    *   **El Cobrador:** Un ticket que cae muy rápido; si lo coges, pierdes puntos (¡hay que esquivarlo!). (Implementado como Factura ✅)
    *   **Tapa de Jamón 5J:** Aparece cada 500 puntos, da 100 puntos pero cae a velocidad terminal. (Implementado como Jamón ✅)
*   **Jefe Final:** Cada 1000 puntos, la pantalla se oscurece y aparece un "Inspector de Sanidad" que lanza prohibiciones que debes esquivar durante 15 segundos.

## Fase 5: Integración Social (Leaderboards) 🚧
*   **Telegram API:** Usar `setGameScore` para actualizar el ranking nativo. (Funcional ✅)
*   **Visualización Nativa:** El mensaje original mostrará automáticamente el Top 3. (Funcional ✅)
*   **Página de Ranking (Web/Mini App):**
    *   Crear una vista dedicada `/game/ranking` con el Top 50 global.
    *   Mostrar fotos de perfil y medallas ganadas junto a la puntuación.
*   **Botón "High Scores":** Configurar el bot para que el botón de "Puntuaciones" del mensaje del juego abra la Mini App en la sección de ranking.
*   **Ranking Post-Partida:** Añadir un botón en la pantalla de Game Over que lleve directamente a la tabla de clasificación.

## Fase 6: Lanzamiento y Marketing 🚀
*   **Trailer:** Pequeño video del gameplay.
*   **Tournament:** Organizar el "I Torneo de Pincho de Oro" con premios en Cuñao Points o Regalos Reales.

## Apéndice: Assets Faltantes (Audio)

Para completar la experiencia auditiva, necesitamos los siguientes archivos de audio en `src/static/game/audio/` (o subidos al bucket):

| Archivo | Descripción | Duración |
| :--- | :--- | :--- |
| **bgm_pasodoble.mp3** | Música de fondo en bucle. Estilo chiptune/8-bit pasodoble. | ~30s (loop) |
| **sfx_crunch.mp3** | Sonido crujiente al comer croqueta. | < 0.5s |
| **sfx_bad.mp3** | Sonido de error/golpe al perder vida. | < 0.5s |
| **sfx_powerup.mp3** | Sonido mágico/celestial al coger carajillo. | < 1s |
| **sfx_cash.mp3** | Sonido de caja registradora o monedas al coger factura. | < 0.5s |
