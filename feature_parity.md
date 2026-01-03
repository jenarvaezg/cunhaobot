# Matriz de Paridad de Funcionalidades - CuñaoBot

Este documento registra las funcionalidades disponibles en cada plataforma integrada con CuñaoBot para asegurar la consistencia de la experiencia de usuario.

| Funcionalidad | Telegram | Slack | Web | Twitter |
| :--- | :---: | :---: | :---: | :---: |
| **IA Conversacional (Roast)** | ✅ (Gemini 2.0) | ✅ (Gemini 2.0) | ❌ | ❌ |
| **Cuñao Vision (Roast Fotos)** | ✅ (Gemini 2.0) | ❌ | ❌ | ❌ |
| **Búsqueda de Frases** | ✅ (Inline) | ✅ (Comandos) | ✅ (Buscador) | ❌ |
| **Envío de Stickers (Imagen)** | ✅ (Inline) | ✅ (Comando/Botón) | ✅ (Visualizar) | ❌ |
| **Envío de Notas de Voz** | ✅ (Inline) | ❌ | ✅ (Reproductor) | ❌ |
| **Perfil de Usuario** | ✅ (Comando) | ✅ (Comando) | ✅ (Página) | ❌ |
| **Puntos y Gamificación** | ✅ | ✅ | ✅ | ❌ |
| **Medallas / Logros** | ✅ | ✅ | ✅ | ❌ |
| **Progreso de Logros** | ✅ | ✅ | ✅ (Barra %) | ❌ |
| **Vinculación de Cuentas** | ✅ | ✅ | ❌ | ❌ |
| **Propuesta de Frases** | ✅ | ❌ | ✅ (Admin) | ❌ |
| **Votación / Moderación** | ❌ | ❌ | ✅ (Admin) | ❌ |
| **Generación Imagen IA (DALL-E/Gemini)** | ✅ (Stars) | ❌ | ✅ (Owner) | ❌ |
| **Estadísticas / Métricas** | ❌ | ❌ | ✅ | ❌ |
| **Publicación Automática** | ❌ | ❌ | ❌ | ✅ (Cron) |
| **App Home / Dashboard** | ❌ | ✅ | ✅ | ❌ |

---

## Detalle por Plataforma

### 🔵 Telegram
* **IA Conversacional:** Paco responde a mensajes directos, menciones en grupos y respuestas (replies).
* **Cuñao Vision:** Roast visual de fotos enviadas por privado o mencionando al bot en grupos.
* **Generación de Pósters:** Comando `/poster` para generar imágenes personalizadas pagando con Telegram Stars.
* **Modo Inline:** Permite buscar y enviar frases cortas, largas, stickers y audios en cualquier chat escribiendo `@CunhaoBot`.
* **Comandos:** `/perfil`, `/link`, `/submit`, `/poster`, `/help`, `/about`, `/stop`.
* **Notificaciones:** El bot te avisa en tiempo real cuando consigues una medalla.

### 🟣 Slack
* **IA Conversacional:** Paco responde a menciones (`@Paco`) y mensajes directos.
* **Interactividad:** Los comandos `/cuñao`, `/sticker` y `/saludo` permiten "barajar" (shuffle) el resultado antes de enviarlo al canal.
* **App Home:** Una pestaña de inicio personalizada con instrucciones y estado del bot.
* **Comandos:** `/cuñao`, `/sticker`, `/saludo`, `/perfil`, `/link`.

### 🌐 Web
* **Exploración:** Listado completo de frases míticas con buscador en tiempo real (HTMX).
* **Perfil Público/Privado:** Visualización detallada de logros, nivel y contribuciones. Opción de ocultar el perfil.
* **Admin Tools:** Gestión de propuestas de frases, votaciones y generación de imágenes por IA para frases existentes.
* **Métricas:** Panel de control con gráficos sobre el uso del bot y rareza de medallas.

### 🐦 Twitter (X)
* **Paco Bot:** Publicación automática de frases célebres (LongPhrases) de forma periódica mediante una tarea programada (cron).
* **Social Sharing:** Soporte completo de Twitter Cards para que las frases y perfiles luzcan bien al ser compartidos.
