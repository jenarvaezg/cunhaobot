# Roadmap de Ideas: cunhaobot 2026

## 1. Modernización: "Paco 2.0" (Nuevas Funcionalidades)
Aprovechar las últimas capacidades de la Bot API para mejorar la interacción y presencia del bot.
* **Telegram Mini App (TMA) 9.0:**
    * **Dashboard de Bar:** Webview en pantalla completa con estética de "Pizarra de Menú" para ver rankings y perfiles de forma interactiva.
    * **Shared Storage & Shortcuts:** Sincronización instantánea y posibilidad de añadir a "Paco" a la pantalla de inicio del móvil.
* **Paco for Business:**
    * Integrar la API de **Business Bots**. Los usuarios con cuenta Business pueden delegar sus respuestas en Paco para que atienda a sus clientes con su sabiduría cuñadil.
* **Reacciones Inteligentes (SetMessageReaction):**
    * Paco reaccionará automáticamente con emojis temáticos (🍺, 🇪🇸, 🥘, 🤡) basándose en el análisis de sentimiento de Gemini sobre los mensajes del grupo.
* **Stories & Social:**
    * Publicar automáticamente "La Perla del Día" en las Stories del bot, con imágenes y encuestas generadas por IA.
* **User Story:** "Como dueño de un taller mecánico con cuenta Business, quiero que Paco responda a mis clientes de Telegram con su toque especial para que sepan quién manda aquí".

## 2. Monetización: "La Economía de Paco" (Features de Pago)
Estrategias para hacer el bot sostenible utilizando Telegram Stars (XTR) y otros métodos.
* **Telegram Stars (Bienes Digitales):**
    * **Gifts (Carajillos Digitales):** Sistema de regalos únicos. Los usuarios pueden enviarse carajillos, copas de coñac o palillos de plata que lucen en el perfil de la Mini App.
    * **Paid Media:** Envío de "Audios Pro" o roasts de Cuñao Vision de alta definición que solo se desbloquean con Stars.
    * **IA Image Generation:** Cobrar una pequeña cantidad de Stars por cada imagen personalizada generada para una frase.
* **Suscripción "V.I.P." (Very Important Paco):**
    * Acceso a voces de TTS premium (Antonio Resines style), prioridad de procesamiento y eliminación de publicidad.
* **Merchandising Directo:**
    * Integración para comprar camisetas o tazas con "tus frases estrella" directamente desde el bot.
* **User Story:** "Como usuario fiel, quiero gastar mis Stars en regalarle un puro digital a mi cuñado del grupo para celebrar que su equipo ha perdido".

## 3. Gamificación: "La Liga de los Cuñados"
* **Concepto:** Sistema de puntos por actividad y calidad de propuestas.
* **Rangos:** De "Aprendiz de Barra" a "Gran Maestro del Palillo".
* **Insignias (Badges):** "Experto en Diésel", "Mili hecha en el Sáhara", "Alicatador de Primera".

---

# Plan de MVP (V1.0: "El Paco Moderno")

**Objetivo:** Relanzar el bot con una funcionalidad estrella y mejorar la UX base.

### Fase 1: Core Multimodal (Completado ✅)
* Implementar `vision_service` utilizando Gemini 2.5 Flash para procesar imágenes.
* Integrar `vision` con `tts_service` para respuestas vocales.
* Comando `/vision` o simplemente detectar fotos en chats privados.

### Fase 2: Modernización UI (Semana 3)
* Crear la primera versión de la **Mini App de Ranking** usando HTMX (integrado en Litestar).
* Implementar el sistema de "Cuñao Points" básico en Datastore.

### Fase 3: Monetización "La Caña" (Semana 4)
* Integrar pagos con Telegram Stars para la generación de imágenes IA.
* Setup de "Support the bot" temático.
