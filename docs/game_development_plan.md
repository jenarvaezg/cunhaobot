# Plan de Desarrollo: Paco's Tapas Runner (Próximos Pasos)

Este documento detalla las mejoras pendientes para profesionalizar el juego y añadir profundidad mecánica.

## Fase 4: Mecánicas Avanzadas (Dificultad y Variedad) 🎮
*   **Sistema de Combos:** Multiplicador de puntos si capturas 3 croquetas seguidas sin fallar. Se activará un texto dinámico: "¡Toma ya!", "¡Fiera!", "¡Nivel Dios!". ✅
*   **Patrones de Lluvia:** En lugar de caída aleatoria, crear "oleadas" temáticas: 🚧
    *   *Ronda de Invitación:* Solo caen croquetas y jamón durante 5 segundos.
    *   *Ataque Moderno:* Lluvia masiva de aguacates y sushi con un solo hueco para pasar.
*   **Nuevos Powerups y Obstáculos:**
    *   🧻 **Servilleta de Bar:** Recupera 1 vida (máximo 3). Solo aparece cuando te queda 1 vida. ✅
    *   ⏱️ **El Vinito/Cañita:** Item especial que añade +10 segundos al cronómetro. ✅
    *   🕵️ **Jefe Final: El Inspector:** Cada 1000 puntos, la pantalla se oscurece y aparece un "Inspector de Sanidad" que lanza prohibiciones que debes esquivar durante 15 segundos.

## Fase 5: Rediseño de Interfaz (De "Cutre" a "Tasca Deluxe") ✅
El objetivo era sustituir el look de "ejemplo de Phaser" por una estética de bar auténtico.

*   **Tipografía de Pizarra:** Usar fuentes que parezcan tiza sobre pizarra negra para el HUD (Score, Tiempo). ✅
*   **HUD Visual:**
    *   Sustituir el texto de vidas por iconos de servilletas dobladas. ✅
    *   Barra de tiempo visual: Una jarra de cerveza que se va vaciando conforme pasa el tiempo. ✅
*   **Pantallas de Menú:**
    *   **Start Screen:** Usar un fondo que parezca una carta de bar con los precios (puntos) de cada tapa. ✅
    *   **Game Over:** Efecto de "Cierre de Persiana" metálica al terminar la partida. ✅
*   **Feedback Visual Pulido:**
    *   Efecto de "Cámara Lenta" (Time Scale) de 0.5s al capturar un Jamón 5J. ✅
    *   Sacudida de pantalla (Shake) más intensa si chocas con un aguacate. ✅
    *   Filtro CRT opcional para darle un toque retro de máquina recreativa de bar. ✅ (Implementado vía post-processing/estilo)

## Fase 6: Social y Retención 🏆
*   **Logros Locales:** Mostrar "Récord Personal" en la pantalla de inicio.
*   **Desafío del Día:** Un multiplicador especial que cambia cada día (ej: "Hoy el sushi puntúa doble").

## Fase 7: Lanzamiento y Marketing 🚀
*   **Trailer:** Video corto con música de pasodoble épica.
*   **Tournament:** Organizar el "I Torneo de Pincho de Oro" con ranking en tiempo real en el canal de Telegram.

---
*Estado actual: Infraestructura, Audio base y Assets 8-bit completados.*
