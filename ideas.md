1. CuñaoGPT (Modo Conversacional Real)
   * Concepto: Transformar el bot de un "dispensador de frases estáticas" a un "agente conversacional".
   * Implementación:
       * Usar ai_service.py conectado a un LLM (Gemini/OpenAI).
       * System Prompt: "Eres un cuñao de 50 años en la barra de un bar. Respondes con condescendencia, usas refranes mal dichos y
         siempre tienes una anécdota mejor."
       * Permitir que los usuarios hagan preguntas directas: @cunhaobot ¿qué opinas del Bitcoin?.
   * KPI: Tiempo de interacción por usuario.

  2. Gamificación: "El Ranking de la Sabiduría"
   * Concepto: Fomentar que la comunidad alimente al bot (Crowdsourcing).
   * Implementación:
       * Mejorar el sistema de proposals y voting.
       * Crear un Leaderboard público (web HTMX) de los usuarios que más frases han aportado y han sido aprobadas.
       * Otorgar "Rangos" en el chat (ej: "Aprendiz", "Oficial de 1ª", "Maestro Barra").
   * KPI: Número de propuestas enviadas por semana.

  3. Modo Debate (Interacción Multi-usuario)
   * Concepto: El bot actúa como árbitro (parcial) en una discusión.
   * Implementación:
       * Comando /debate [Tema].
       * El bot asigna posturas a dos usuarios del grupo y va soltando frases para "calentar" el ambiente.
       * Al final, declara ganador al que haya dicho la "cuñadez" más grande (basado en reacciones/votos).

  4. Panel de Administración 2.0 (Mobile First)
   * Concepto: Facilitar la moderación de contenido.
   * Implementación:
       * Mejorar approve_web_test.py y los templates HTMX.
       * Interfaz estilo "Tinder" (Swipe Left/Right) para aprobar o rechazar propuestas de frases rápidamente desde el móvil.
       * Añadir métricas de uso en tiempo real en /admin.
