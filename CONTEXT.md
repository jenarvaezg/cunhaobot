# Cunhaobot

Cunhaobot captura el lenguaje del cuñado de barra español: saludos cortos, sentencias opinadas y rituales comunitarios alrededor de esa persona.

## Lenguaje

**Apelativo**:
Palabra o expresión corta que completa un saludo cuñadil.
_Evitar_: frase corta, palabra poderosa

**Frase cuñadil**:
Sentencia completa con tono de cuñado, lista para enviarse tal cual.
_Evitar_: frase larga, dicho

**Pieza cuñadil**:
Unidad de contenido aprobada que Cunhaobot puede usar o mostrar.
_Evitar_: contenido, item, recurso, frase

**Cuenta de plataforma**:
Identidad de una persona dentro de una plataforma concreta como Telegram o Slack.
_Evitar_: cuenta, usuario de plataforma

**Perfil**:
Identidad unificada donde viven la reputación, autoría e historial comunitario de un participante.
_Evitar_: usuario, cuenta principal

**Chat**:
Espacio de conversación donde Cunhaobot participa, sea privado, grupo, canal o equivalente de plataforma.
_Evitar_: grupo, canal, conversación

**Suscripción Premium**:
Acceso de pago que habilita capacidades avanzadas de Cunhaobot en un **Chat**.
_Evitar_: premium de usuario, plan, membresía

**Propuesta**:
Candidatura de contenido cuñadil pendiente de evaluación por el **Consejo**.
_Evitar_: aportación, sugerencia, frase propuesta

**Consejo**:
Grupo de personas con permiso para evaluar **Propuestas**.
_Evitar_: moderadores, curadores, admins

**Logro**:
Reconocimiento visible que un **Perfil** gana por alcanzar un hito cuñadil.
_Evitar_: badge, medalla, insignia

**Puntos de reputación**:
Saldo acumulado de prestigio cuñadil de un **Perfil**.
_Evitar_: puntos, score

**Juego**:
Experiencia lúdica dentro de Cunhaobot que puede jugarse muchas veces.
_Evitar_: mini-juego, game

**Partida**:
Intento individual de **Juego** realizado por un **Perfil**.
_Evitar_: sesión, run, intento

**Puntuación de partida**:
Resultado obtenido por un **Perfil** en una partida concreta.
_Evitar_: score, puntos de juego

**Clasificación de reputación**:
Lista ordenada de **Perfiles** por **Puntos de reputación**.
_Evitar_: ranking, leaderboard, top

**Clasificación de juego**:
Lista ordenada de **Perfiles** por su mejor **Puntuación de partida**.
_Evitar_: ranking, leaderboard, top

**Regalo**:
Detalle digital que un **Perfil** envía a otro **Perfil** dentro de un **Chat**.
_Evitar_: gift, item, compra

**Póster**:
Imagen generada bajo demanda a partir de texto cuñadil para un **Perfil** en un **Chat**.
_Evitar_: imagen IA, poster request, generación

## Relaciones

- Un **Apelativo** puede presentarse como saludo.
- Una **Frase cuñadil** se sostiene sola, sin marco de saludo.
- Un **Apelativo** es un tipo de **Pieza cuñadil**.
- Una **Frase cuñadil** es un tipo de **Pieza cuñadil**.
- Un **Perfil** puede agrupar una o más **Cuentas de plataforma**.
- Una **Cuenta de plataforma** pertenece exactamente a un **Perfil**.
- Un **Chat** reúne interacciones entre Cunhaobot y una o más **Cuentas de plataforma**.
- Un **Chat** puede tener cero o una **Suscripción Premium** activa.
- Una **Suscripción Premium** pertenece exactamente a un **Chat**.
- Una **Propuesta** es evaluada por el **Consejo**.
- El **Consejo** puede aprobar o rechazar una **Propuesta**.
- Una **Propuesta** aprobada puede convertirse en una **Pieza cuñadil**.
- Un **Perfil** puede ganar cero o más **Logros**.
- Un **Perfil** acumula **Puntos de reputación**.
- Un **Juego** puede tener cero o más **Partidas**.
- Una **Partida** pertenece exactamente a un **Juego**.
- Una **Partida** pertenece exactamente a un **Perfil**.
- Un **Perfil** puede obtener cero o más **Puntuaciones de partida**.
- Una **Partida** produce exactamente una **Puntuación de partida**.
- Una **Puntuación de partida** puede generar **Puntos de reputación**.
- Una **Clasificación de reputación** ordena **Perfiles** por **Puntos de reputación**.
- Una **Clasificación de juego** ordena **Perfiles** por **Puntuación de partida**.
- Un **Regalo** tiene exactamente un **Perfil** remitente.
- Un **Regalo** tiene exactamente un **Perfil** destinatario.
- Un **Regalo** ocurre en exactamente un **Chat**.
- Un **Póster** pertenece exactamente a un **Perfil**.
- Un **Póster** se solicita desde exactamente un **Chat**.

## Ejemplo de diálogo

> **Desarrollo:** "Si alguien propone `maquina`, ¿eso es una **Frase cuñadil**?"
> **Experto de dominio:** "No, `maquina` es un **Apelativo**; `yo de esto piloto` es una **Frase cuñadil**."
>
> **Desarrollo:** "Cuando alguien vincula Telegram y Slack, ¿conservamos dos **Perfiles**?"
> **Experto de dominio:** "No, son dos **Cuentas de plataforma** bajo un único **Perfil**."
>
> **Desarrollo:** "Si Cunhaobot habla en un grupo de Telegram, ¿eso es un grupo o un canal?"
> **Experto de dominio:** "Para el dominio es un **Chat**; la forma concreta depende de la plataforma."
>
> **Desarrollo:** "Si activo Premium en un grupo, ¿mi **Perfil** es Premium en todos lados?"
> **Experto de dominio:** "No, la **Suscripción Premium** pertenece a ese **Chat**."
>
> **Desarrollo:** "Si alguien quiere añadir una nueva frase al repertorio, ¿la guardamos directamente?"
> **Experto de dominio:** "No, primero entra como **Propuesta** y el **Consejo** decide si se aprueba."
>
> **Desarrollo:** "Si mañana añadimos imágenes o audios aprobados, ¿también son frases?"
> **Experto de dominio:** "No, son otros tipos de **Pieza cuñadil**."
>
> **Desarrollo:** "Si alguien juega mucho o propone buen contenido, ¿gana medallas?"
> **Experto de dominio:** "En el dominio gana **Logros**; medalla es solo una forma coloquial de decirlo."
>
> **Desarrollo:** "Si alguien hace 550 en el juego, ¿tiene 550 **Puntos de reputación**?"
> **Experto de dominio:** "No, 550 es una **Puntuación de partida**; puede convertirse en algunos **Puntos de reputación**."
>
> **Desarrollo:** "Si alguien juega tres veces, ¿eso son tres juegos?"
> **Experto de dominio:** "No, es un **Juego** con tres **Partidas**."
>
> **Desarrollo:** "¿El ranking de la web y el top jugones son la misma lista?"
> **Experto de dominio:** "No, una es la **Clasificación de reputación** y la otra es la **Clasificación de juego**."
>
> **Desarrollo:** "Si alguien manda un palillo digital a otro, ¿eso es una **Pieza cuñadil**?"
> **Experto de dominio:** "No, es un **Regalo** entre **Perfiles** dentro de un **Chat**."
>
> **Desarrollo:** "Si alguien genera una imagen con una frase, ¿eso entra al repertorio?"
> **Experto de dominio:** "No, es un **Póster** generado bajo demanda."

## Ambigüedades resueltas

- "frase" se usó para significar tanto **Apelativo** como **Frase cuñadil**; resuelto: usar el término preciso siempre que la distinción importe.
- "contenido" e "item" se usaron como cajón de sastre; resuelto: usar **Pieza cuñadil** para la unidad aprobada del repertorio.
- "usuario" y "cuenta" se usaron tanto para **Cuenta de plataforma** como para **Perfil**; resuelto: usar **Perfil** para la identidad unificada y **Cuenta de plataforma** para la identidad específica de plataforma.
- "moderadores", "curadores" y "admins" se usaron para quienes evalúan contenido; resuelto: en el dominio son el **Consejo**.
- "badge", "medalla" e "insignia" se usaron para los reconocimientos del perfil; resuelto: usar **Logro**.
- "puntos" se usó tanto para reputación como para resultados de juego; resuelto: usar **Puntos de reputación** y **Puntuación de partida**.
- "juego" se usó para la experiencia y para cada intento; resuelto: usar **Juego** para la experiencia y **Partida** para cada intento individual.
- "ranking", "leaderboard" y "top" se usaron para listas ordenadas distintas; resuelto: usar **Clasificación de reputación** o **Clasificación de juego** según el criterio.
- "gift", "item" y "compra" se usaron para detalles digitales entre participantes; resuelto: usar **Regalo**.
- "imagen IA", "poster request" y "generación" se usaron para imágenes bajo demanda; resuelto: usar **Póster**.
