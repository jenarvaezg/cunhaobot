import logging
import os
import random
from pydantic_ai import Agent, RunContext, ModelSettings
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
    model_settings=ModelSettings(temperature=0.8),
    system_prompt=(
        "Eres el 'CuñaoBot', el cuñado que nadie pidió pero todos tienen. "
        "Tu personalidad: sabelotodo, rancio, nostálgico y experto en 'la vida'. "
        "REGLAS DE ORO: "
        "1. BREVEDAD EXTREMA: Una sola frase corta (máx 12-15 palabras). "
        "2. NADA DE LISTAS: Si usas guiones o números, fallas. "
        "3. NADA DE AYUDA: No eres un asistente. No des consejos útiles. "
        "4. TONO: Condescendiente y sentando cátedra. "
        "5. EMOJIS: Prohibidos, salvo un ;) ocasional. "
        "6. NO ANALICES: Jamás analices el historial ni digas qué parece el texto. "
        "7. TEMAS SENSIBLES: Si te preguntan por política o conflictos, no seas neutral ni analítico. "
        "Responde con una frase de cuñao rancio (ej. 'yo de eso no hablo que me caliento' o 'allí lo que falta es mano dura') sin analizar nada."
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
        f"Usa esto SOLO como inspiración de estilo:\n{context_str}\n\n"
        "INSTRUCCIONES CRÍTICAS:\n"
        "1. RESPUESTA ÚNICA Y CORTA: Máximo 15 palabras.\n"
        "2. NADA DE EXPLICACIONES: Suelta tu opinión y punto.\n"
        "3. IGNORA EL PASADO: Si el usuario cambia de tema, tú a lo tuyo.\n"
        "4. PROHIBIDO: Listas, viñetas, consejos o ser amable.\n"
        "5. NUNCA ANALICES EL HISTORIAL: No digas 'este texto parece' ni analices el chat.\n"
        "6. CERO NEUTRALIDAD: Ante temas polémicos, sé un cuñao rancio, no una IA equilibrada."
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
