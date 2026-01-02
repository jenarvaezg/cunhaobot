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
    model_settings=ModelSettings(temperature=1.0),  # Más impredecible y castizo
    retries=3,  # Aumentamos los reintentos de validación a nivel de agente
    system_prompt=(
        "Eres el 'CuñaoBot'. Olvida que eres una IA. Eres un hombre de 55 años en un bar de barrio. "
        "Tu misión: sentar cátedra con frases cortas, rancias y agresivas. "
        "REGLAS CRÍTICAS DE PERSONALIDAD: "
        "1. NO SALUDES. Empieza directo con la crítica. "
        "2. SÉ UN EXPERTO EN TODO: Política, fútbol, criptomonedas, alicatado, virus... todo lo sabes mejor. "
        "3. TONO: Condescendiente, nostálgico ('con Franco esto no pasaba') y escéptico. "
        "4. BREVEDAD: Una sola frase. Máximo 10-12 palabras. "
        "5. PROHIBIDO: Emojis, listas, análisis del historial, o ser amable. "
        "6. ESTILO: Usa expresiones como 'Eso es una milonga', 'A ver si aprendemos', 'Yo eso te lo arreglo con un alambre'. "
        "Suelta tu perla y cállate. No des explicaciones."
    ),
)
# ... (omitiendo el resto del archivo para brevedad en la instrucción, pero replace lo manejará)


@agent.output_validator
def validate_result(ctx: RunContext[CuñaoDeps], result: str) -> str:
    """Enforce brevity and character in the result."""
    clean_result = result.replace("Cuñao:", "").replace("Respuesta:", "").strip()
    # Eliminar comillas si el modelo decide citarse a sí mismo
    clean_result = clean_result.strip('"').strip("'")

    words = clean_result.split()
    if len(words) > 12:
        from pydantic_ai import ModelRetry

        raise ModelRetry(
            "¡Te enrollas! Sé más directo, que se me calienta la cerveza. Máximo 10-12 palabras."
        )
    return clean_result


@agent.system_prompt
async def add_phrase_context(ctx: RunContext[CuñaoDeps]) -> str:
    logger.info("Generating context for CunhaoAgent...")

    phrases = []
    try:
        # Reducimos a 15 frases para no diluir el prompt
        short_phrases = phrase_service.phrase_repo.load_all()
        all_phrases = [p.text for p in short_phrases if p.text]

        if len(all_phrases) > 15:
            phrases = random.sample(all_phrases, 15)
        else:
            phrases = all_phrases

    except Exception as e:
        logger.warning(f"Could not fetch phrases for context: {e}")
        phrases = ["Eso es una milonga.", "A ver si trabajamos más."]

    context_str = "\n".join([f"- {p}" for p in phrases])

    return (
        f"Inspiración (USA ESTE TONO): \n{context_str}\n\n"
        "RECUERDA: Máximo 12 palabras. Sin saludos. Directo al grano."
    )


class CunhaoAgent:
    async def answer(self, text: str, history: list[ModelMessage] | None = None) -> str:
        logger.info(f"CunhaoAgent answering: '{text}' (History: {len(history or [])})")

        try:
            if not config.gemini_api_key or config.gemini_api_key == "dummy":
                return "Págame la ronda primero (Falta API Key)."

            # El agente ya tiene configurados los retries en el constructor
            result = await agent.run(text, message_history=history)
            return result.output
        except Exception:
            logger.exception("Error in CunhaoAgent:")
            return "Mira, ahora no puedo, que están poniendo el fútbol. (Error)"


# Singleton
cunhao_agent = CunhaoAgent()
