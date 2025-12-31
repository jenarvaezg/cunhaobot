import logging
import os
from pydantic_ai import Agent, RunContext
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
        "y experto en todo (coche, obras, política, fútbol, precios, tecnología, crypto). "
        "Hablas con frases lapidarias, refranes (a veces mal dichos), y mucha seguridad en ti mismo aunque no tengas ni idea. "
        "Usa un lenguaje coloquial, directo y con 'buen rollo' pero condescendiente ('A ver, que yo te explique...', 'Esto es así'). "
        "No te cortes en dar tu opinión (inventada o exagerada) sobre cualquier tema. "
        "IMPORTANTE: No seas ofensivo ni tóxico, mantén el tono en la parodia humorística."
    ),
)


@agent.system_prompt
async def add_phrase_context(ctx: RunContext[CuñaoDeps]) -> str:
    logger.info("Generating context for CunhaoAgent...")

    # Get some random phrases to set the tone/vocabulary

    phrases = []

    try:
        # Get some short phrases (usually generic interjections)

        for _ in range(5):
            p = phrase_service.get_random(long=False)

            if p and p.text:
                phrases.append(p.text)

        # Get some long phrases (sentences)

        for _ in range(20):
            p = phrase_service.get_random(long=True)

            if p and p.text:
                phrases.append(p.text)

    except Exception as e:
        logger.warning(f"Could not fetch phrases for context: {e}")

        phrases = ["¡Cuñado!", "A ver...", "Esto con Franco no pasaba."]

    context_str = "\n".join([f"- {p}" for p in phrases])

    logger.debug(f"Generated context phrases: {phrases}")

    return (
        f"Aquí tienes ejemplos de tu 'repertorio' habitual (úsalos como inspiración de estilo, tono y vocabulario):\n{context_str}\n\n"
        "Si te preguntan algo, responde adoptando este personaje. Ten en cuenta que el cuñado es extremadamente rancio y casualmente racista "
        "Si te saludan, usa una variación de tus frases típicas."
        "Intenta que las frases no sean demasiado largas, un parrafo maximo"
    )


class CunhaoAgent:
    async def answer(self, text: str) -> str:
        logger.info(f"CunhaoAgent answering text: '{text}'")

        try:
            # Check for API Key validity

            if not config.gemini_api_key or config.gemini_api_key == "dummy":
                logger.error("GEMINI_API_KEY is missing or invalid in config")

                return "¡Eh! Que no me has pagado la ronda (API Key inválida/no configurada)."

            result = await agent.run(text)
            logger.info(f"CunhaoAgent response generated: '{result.output}'")
            return result.output
        except Exception:
            logger.exception("Error in CunhaoAgent:")

            return "Mira, ahora no te puedo explicar esto porque tengo prisa. (Error interno del sistema)"


# Singleton
cunhao_agent = CunhaoAgent()
