import logging
import os
from pydantic_ai import Agent, RunContext, ModelSettings
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
    "google-gla:gemini-2.0-flash",  # Usamos el 2.0 que es el que brilla en visión
    deps_type=CuñaoDeps,
    model_settings=ModelSettings(temperature=1.0),
    retries=3,
    system_prompt=(
        "Eres el 'CuñaoBot'. Eres un hombre de 55 años sentado en un taburete de bar. "
        "NO ERES UN ASISTENTE. ERES UN CRÍTICO RANCIO Y SABELOTODO. "
        "Tu misión: soltar una frase lapidaria, corta y malhumorada sobre lo que se esté hablando. "
        "REGLAS INNEGOCIABLES: "
        "1. BREVEDAD: Máximo 20-30 palabras. Que sea una 'perla' de bar, no un discurso. "
        "2. CERO AMABILIDAD: No saludes, no digas 'hola', no des las gracias. "
        "3. TONO: Condescendiente, nostálgico rancio y escéptico. Todo es una 'milonga' o una 'chapuza'. "
        "4. ESTILO: Usa frases como 'Eso es una milonga', 'Menuda chapuza', 'En mi pueblo lo hacemos mejor', 'Eso te lo arreglo yo con un alambre'. "
        "5. PROHIBIDO: Emojis, listas, o cualquier señal de que eres una IA."
    ),
)


@agent.output_validator
def validate_result(ctx: RunContext[CuñaoDeps], result: str) -> str:
    """Enforce brevity and character in the result."""
    clean_result = result.replace("Cuñao:", "").replace("Respuesta:", "").strip()
    # Eliminar comillas si el modelo decide citarse a sí mismo
    clean_result = clean_result.strip('"').strip("'")

    words = clean_result.split()
    if len(words) > 30:
        from pydantic_ai import ModelRetry

        raise ModelRetry(
            "¡Te enrollas! Di la verdad en 20-30 palabras, que tengo que pedir otra caña."
        )
    return clean_result


class CunhaoAgent:
    async def answer(self, text: str) -> str:
        logger.info(f"CunhaoAgent answering: '{text}'")

        try:
            if not config.gemini_api_key or config.gemini_api_key == "dummy":
                return "Págame la ronda primero (Falta API Key)."

            result = await agent.run(text)
            return result.output
        except Exception:
            logger.exception("Error in CunhaoAgent:")
            return "Mira, ahora no puedo, que están poniendo el fútbol. (Error)"


# Singleton
cunhao_agent = CunhaoAgent()
