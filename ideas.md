# Roadmap de Ideas: cunhaobot 2026

## 1. Modernización: "Paco 2.0" (Telegram Features)
El bot original es de 2019. Toca aprovechar las nuevas APIs.
* **Mini App (TMA):** Un Dashboard con estética de "Menú del Día" para ver el ranking de frases, proponer nuevas y ver el perfil del usuario (insignias, puntos).
* **Reacciones:** El bot debe reaccionar automáticamente con emojis castizos (🍺, 🥘, 🇪🇸) a ciertos mensajes.
* **Stories:** Si el bot es admin de un canal/grupo, publicar la "Frase del Día" en Stories.
* **User Story:** "Como usuario, quiero abrir el ranking en una webview dentro de Telegram para no hacer scroll infinito en un mensaje de texto".

## 2. Monetización: "Invita a Paco a una caña"
Monetización orgánica y temática.
* **Telegram Stars:** Pago de "Stars" para:
    * Generar una imagen personalizada con IA basada en una frase.
    * Roast visual prioritario (Cuñao Vision Pro).
    * Quitar publicidad (si se añade en el futuro).
* **Merchandising Directo:** Integración con Printful/Redbubble para comprar una camiseta con tu frase favorita directamente desde el bot.
* **User Story:** "Como usuario fiel, quiero invitar a una 'caña' (0.99€) al bot para agradecerle las risas y desbloquear la voz premium de Antonio Resines (o similar)".

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
