# Plan de Desarrollo: Paco's Tapas Runner

Este plan detalla los pasos para convertir el prototipo actual en un juego digno de ganar una Game Jam.

## Fase 1: Infraestructura Core ✅
*   **Registro del juego:** `palillo_cunhao` registrado en BotFather. ✅
*   **Bot Handler:** Comando `/jugar` y gestión de callbacks. ✅
*   **Backend:** API de puntuación con validación SHA-256 e integración con Datastore. ✅
*   **Web Integration:** Acceso desde `/game` para debug y juego libre. ✅

## Fase 2: El "Juice" y Pulido Visual 🚧
*   **Sustitución de Assets:**
    *   Cambiar formas geométricas por **Pixel Art 8-bit**.
    *   Animación de "Squash & Stretch" en el palillo al moverse.
    *   Efecto de rotación/balanceo en las tapas al caer.
*   **Background Dinámico:** Fondo de azulejos con efecto *Parallax* (que se mueva ligeramente al mover el palillo).
*   **Sistema de Partículas:**
    *   Migas doradas al pinchar una croqueta.
    *   Chispas moradas y rastro de humo al usar el Carajillo.
    *   Efecto de "Splat" verde al chocar con un aguacate.
*   **UI Feedback:**
    *   Hacer que el score "salte" (tween de escala) al puntuar.
    *   Flash de pantalla y vibración (vibrate API) al perder vida.

## Fase 3: Audio y Narrativa de Bar 🔊
*   **Música Evolutiva (Strudel):**
    *   Mejorar el patrón musical para que sea un Pasodoble épico.
    *   Hacer que el tempo (CPM) suba ligeramente cada 100 puntos.
*   **Efectos de Sonido (SFX):**
    *   Sonido de "¡Crunch!" al capturar tapas.
    *   Sonido de "¡Error!" metálico al chocar con obstáculos.
*   **Voice Acting (Paco Clips):**
    *   "¡Mákina!" al conseguir un combo de 5 tapas.
    *   "¡Oído cocina!" al activar el carajillo.
    *   "¡Vete a un Starbucks!" al morir por un aguacate.

## Fase 4: Mecánicas Avanzadas (Dificultad y Variedad) 🎮
*   **Sistema de Combos:** Multiplicador de puntos si capturas 3 croquetas seguidas sin fallar.
*   **Patrones de Lluvia:** En lugar de caída aleatoria, crear "oleadas" (ej. una fila de aguacates con un solo hueco).
*   **Nuevos Elementos:**
    *   **El Cobrador:** Un ticket que cae muy rápido; si lo coges, pierdes puntos (¡hay que esquivarlo!).
    *   **Tapa de Jamón 5J:** Aparece cada 500 puntos, da 100 puntos pero cae a velocidad terminal.
*   **Jefe Final:** Cada 1000 puntos, la pantalla se oscurece y aparece un "Inspector de Sanidad" que lanza prohibiciones que debes esquivar durante 15 segundos.

## Fase 4: Integración Social (Leaderboards) 🚧
*   **Telegram API:** Usar `setGameScore` para actualizar el ranking nativo. (Funcional ✅)
*   **Visualización Nativa:** El mensaje original mostrará automáticamente el Top 3. (Funcional ✅)
*   **Página de Ranking (Web/Mini App):**
    *   Crear una vista dedicada `/game/ranking` con el Top 50 global.
    *   Mostrar fotos de perfil y medallas ganadas junto a la puntuación.
*   **Botón "High Scores":** Configurar el bot para que el botón de "Puntuaciones" del mensaje del juego abra la Mini App en la sección de ranking.
*   **Ranking Post-Partida:** Añadir un botón en la pantalla de Game Over que lleve directamente a la tabla de clasificación.

## Fase 6: Lanzamiento y Marketing 🚀
*   **Trailer:** Pequeño video del gameplay con la música de Strudel.
*   **Tournament:** Organizar el "I Torneo de Pincho de Oro" con premios en Cuñao Points o Regalos Reales.

## Apéndice: Guía de Assets y Prompts (IA)

Para mantener la coherencia, todos los assets deben generarse con el estilo **"16-bit pixel art, isolated on transparent background, retro video game style"**.

### A. Sprites (Objetos del juego)
| Asset | Función | Prompt Sugerido |
| :--- | :--- | :--- |
| **Palillo** | Jugador | *16-bit pixel art, isolated wooden toothpick, simple design, retro video game sprite, white background.* |
| **Croqueta** | Tapa (+10) | *16-bit pixel art, golden brown Spanish croquette, crunchy texture, isolated, retro video game sprite.* |
| **Jamón 5J** | Tapa (+100) | *16-bit pixel art, high quality slice of Iberian ham, red and white marbling, isolated, retro video game sprite.* |
| **Aguacate** | Obstáculo (-1V) | *16-bit pixel art, sliced green avocado with pit, hipster aesthetic, isolated, retro video game sprite.* |
| **Sushi** | Obstáculo (-1V) | *16-bit pixel art, salmon nigiri sushi, isolated, retro video game sprite.* |
| **Ticket** | Obstáculo (-Pts) | *16-bit pixel art, long white restaurant receipt, paper texture, isolated, retro video game sprite.* |
| **Carajillo** | Power-up | *16-bit pixel art, carajillo coffee in a small glass, layers of coffee and brandy, isolated, retro video game sprite.* |
| **Servilleta** | Vida (UI) | *16-bit pixel art, white square bar napkin with small red logo, 'Gracias por su visita' style, isolated.* |

### B. Entorno (Backgrounds)
| Asset | Función | Prompt Sugerido |
| :--- | :--- | :--- |
| **Azulejos** | Fondo Parallax | *Seamless pixel art pattern of old Spanish bar wall tiles, white and blue patterns, slightly aged, 8-bit style.* |
| **Barra** | Suelo/Base | *Pixel art texture of a stainless steel bar counter, scratched metal, retro 16-bit style, top-down view.* |

### C. Personajes Especiales
| Asset | Función | Prompt Sugerido |
| :--- | :--- | :--- |
| **Inspector** | Jefe Final | *16-bit pixel art character, man with mustache, wearing a suit and holding a clipboard, angry expression, retro game boss.* |
