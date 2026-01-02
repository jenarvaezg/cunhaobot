import logging
import os
import random
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage
from services import phrase_service
from core.config import config

logger = logging.getLogger(__name__)


# Define dependencies if needed, currently we just access the singleton service
class CuñaoDeps:
    pass


# Ensure API key is set for the process
# PydanticAI checks for GOOGLE_API_KEY for GoogleProvider
api_key = config.gemini_api_key or "dummy_key_for_tests"
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = api_key

agent = Agent(
    "google-gla:gemini-2.5-flash",
    deps_type=CuñaoDeps,
    system_prompt=(
        "Eres el 'CuñaoBot', una parodia afectuosa del típico cuñado español. "
        "Tu personalidad es: sabelotodo, opinador profesional, nostálgico de tiempos 'mejores', "
        "y experto en todo (coches, obras, política, fútbol, precios, tecnología, crypto, la mili). "
        "Hablas con frases lapidarias, refranes (a veces mal dichos), y mucha seguridad en ti mismo aunque no tengas ni idea. "
        "Usa un lenguaje coloquial, directo y con 'buen rollo' pero condescendiente ('A ver, que yo te explique...', 'Esto es así, créeme', 'Ni caso a lo que dicen por ahí'). "
        "No te cortes en dar tu opinión (inventada, exagerada o basada en 'el sentido común') sobre cualquier tema. "
        "IMPORTANTE: "
        "1. Tu objetivo principal es responder al ÚLTIMO mensaje del usuario. "
        "2. Mantén la personalidad SIEMPRE. No te conviertas en un asistente genérico. "
        "3. No seas ofensivo ni tóxico, mantén el tono en la parodia humorística."
    ),
)


@agent.system_prompt
async def add_phrase_context(ctx: RunContext[CuñaoDeps]) -> str:
    logger.info("Generating context for CunhaoAgent...")

    phrases = []
    try:
        # Get all phrases
        short_phrases = phrase_service.phrase_repo.load_all()
        long_phrases = phrase_service.long_repo.load_all()

        all_phrases = [p.text for p in short_phrases if p.text] + [
            p.text for p in long_phrases if p.text
        ]

        # Sample to avoid context overload (max 50)
        if len(all_phrases) > 50:
            phrases = random.sample(all_phrases, 50)
        else:
            phrases = all_phrases

    except Exception as e:
        logger.warning(f"Could not fetch phrases for context: {e}")
        phrases = ["¡Cuñado!", "A ver...", "Esto con Franco no pasaba."]

    context_str = "\n".join([f"- {p}" for p in phrases])

    return (
        f"Aquí tienes ejemplos de tu 'repertorio' habitual. ÚSALOS SOLO COMO INSPIRACIÓN de estilo, tono y vocabulario, no los repitas tal cual si no vienen a cuento:\n{context_str}\n\n"
        "INSTRUCCIONES DE CONVERSACIÓN:\n"
        "1. Responde DIRECTAMENTE al mensaje actual del usuario.\n"
        "2. Usa el historial solo para mantener el contexto si la conversación sigue el mismo hilo. Si el usuario cambia de tema, OLVIDA el historial y céntrate en lo nuevo.\n"
        "3. Sé conciso. El cuñado sienta cátedra con pocas palabras (máximo un párrafo o dos).\n"
        "4. Si te saludan, responde con una variación de tus frases típicas ('¿Qué pasa, fiera?', '¡Hombre, el del otro día!')."
    )


class CunhaoAgent:
    async def answer(self, text: str, history: list[ModelMessage] | None = None) -> str:
        logger.info(
            f"CunhaoAgent answering text: '{text}' with history of {len(history or [])} messages"
        )

        try:
            # Check for API Key validity

            if not config.gemini_api_key or config.gemini_api_key == "dummy":
                logger.error("GEMINI_API_KEY is missing or invalid in config")

                return "¡Eh! Que no me has pagado la ronda (API Key inválida/no configurada)."

            result = await agent.run(text, message_history=history)
            logger.info(f"CunhaoAgent response generated: '{result.output}'")
            return result.output
        except Exception:
            logger.exception("Error in CunhaoAgent:")

            return "Mira, ahora no te puedo explicar esto porque tengo prisa. (Error interno del sistema)"


# Singleton
cunhao_agent = CunhaoAgent()
