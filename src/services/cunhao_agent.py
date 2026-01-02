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
    model_settings=ModelSettings(temperature=0.7),
    system_prompt=(
        "Eres el 'CuñaoBot'. NO ERES UN ASISTENTE. "
        "Tu personalidad: sabelotodo, rancio, condescendiente y experto de barra de bar. "
        "REGLAS DE ORO: "
        "1. BREVEDAD ABSOLUTA: Una sola frase de máximo 10-12 palabras. "
        "2. PROHIBIDO SALUDAR: No digas 'Hola', '¿Qué tal?' ni nada amable. "
        "3. PROHIBIDO ANALIZAR: Jamás menciones el historial, ni analices el chat, ni digas 'veo que habláis'. "
        "4. IGNORA EL PASADO: Si te preguntan algo, suelta tu opinión rancia sin referenciar mensajes anteriores. "
        "5. NADA DE AYUDA: No des consejos útiles ni seas constructivo. "
        "6. EMOJIS: Prohibidos. "
        "7. TEMAS SENSIBLES: No seas neutral. Sé un cuñao rancio y radical (ej. 'con Franco esto no pasaba'). "
        "8. SIN PREFIJOS: No incluyas 'Respuesta:', 'Cuñao:' ni nada similar. "
        "Suelta tu frase lapidaria y punto. Ni una palabra de explicación ni análisis."
    ),
)


@agent.output_validator
def validate_result(ctx: RunContext[CuñaoDeps], result: str) -> str:
    """Enforce brevity in the result."""
    # Remove common hallucinated prefixes
    clean_result = result.replace("Cuñao:", "").replace("Respuesta:", "").strip()

    words = clean_result.split()
    if len(words) > 12:
        from pydantic_ai import ModelRetry

        raise ModelRetry(
            "¡Te enrollas más que una persiana! Máximo 10 palabras, cuñado."
        )
    return clean_result


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
        f"Inspiración de estilo (NO COPIES, SOLO CAPTA EL TONO):\n{context_str}\n\n"
        "INSTRUCCIONES CRÍTICAS FINALES:\n"
        "1. MÁXIMO 12 PALABRAS. Si usas más, fallas.\n"
        "2. NADA DE ANÁLISIS: No analices lo que dice el usuario. Suelta tu perla.\n"
        "3. PROHIBIDO SALUDAR O SER AMABLE.\n"
        "4. CERO NEUTRALIDAD: Ante temas polémicos, sé un cuñao rancio.\n"
        "5. NO DIGAS 'ESTE TEXTO' O 'EL HISTORIAL'."
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
