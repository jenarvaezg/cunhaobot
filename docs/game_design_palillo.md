# GDD: Paco's Tapas Runner: "El Desafío del Palillo"

## 1. Concepto de Juego
Catching game 2D de ritmo rápido para Telegram Gaming Platform. El jugador controla un **Palillo de Dientes** que debe pinchar tapas tradicionales y evitar obstáculos "modernos".

## 2. Gameplay Loop
1.  **Movimiento:** El jugador desliza el Palillo horizontalmente en la base de la pantalla.
2.  **Objetivo:** Capturar objetos que caen desde la parte superior.
3.  **Dificultad:** La velocidad aumenta cada 200 puntos.
4.  **Fin de partida:** Se pierden las 3 vidas (servilletas) al tocar obstáculos o al dejar pasar 3 tapas especiales (Jamón).

### Elementos
*   **Positivos:** Croqueta (+10), Boquerón (+25), Jamón (+50).
*   **Negativos:** Tostada de Aguacate (Muerte instantánea), Agua (Ralentiza), Sushi (-1 vida).
*   **Power-up (Carajillo):** Invencibilidad y doble puntuación durante 8 segundos.

## 3. Retención y Social
*   **Leaderboard Nativo:** Integrado en el chat de Telegram.
*   **Rachas (La Parroquia):** Jugar diariamente otorga un multiplicador acumulativo (max +50%).
*   **Integración:** Los puntos del juego se convierten en "Cuñao Points" para el bot principal.

## 4. Estética
*   **Arte:** Pixel Art 8-bit.
*   **Escenario:** Barra de bar metálica con azulejos de fondo.
*   **Audio:**
    *   **Música:** Pasodoble estilo chiptune (pendiente).
    *   **Voces:** Saludos y frases de "cuñao" generadas por IA (TTS) al inicio y al final de la partida.
    *   **SFX:** Sonidos de "crunch", caja registradora y golpes.
