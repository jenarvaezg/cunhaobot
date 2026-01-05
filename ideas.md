# Roadmap de Ideas: cunhaobot 2026

## 1. Monetización: "La Economía de Paco" (Features de Pago)
Estrategias para hacer el bot sostenible utilizando Telegram Stars (XTR) y otros métodos.
* **Telegram Stars (Bienes Digitales):**
    * **Gifts (Carajillos Digitales):** Sistema de regalos únicos. Los usuarios pueden enviarse carajillos, copas de coñac o palillos de plata que lucen en el perfil de la Mini App.
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

### Fase 2: Modernización UI (Completado ✅)
* Crear la primera versión de la **Mini App de Ranking** usando HTMX (integrado en Litestar).
* Implementar el sistema de "Cuñao Points" básico en Datastore.

### Fase 3: Monetización "La Caña" (En Progreso 🚧)
* Integrar pagos con Telegram Stars para la generación de imágenes IA (/poster) (Completado ✅).
* Implementar Suscripción Premium Mensual (100 Stars) para desbloquear features de IA (/premium) (Completado ✅).
* Setup de "Support the bot" temático.
