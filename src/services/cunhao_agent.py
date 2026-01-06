import logging
import os
from pydantic_ai import Agent, RunContext, ModelSettings
from pydantic_ai.models.test import TestModel

logger = logging.getLogger(__name__)


# Define dependencies if needed
class CunhaoDeps:
    pass


def get_cunhao_agent() -> Agent[CunhaoDeps, str]:
    model = os.environ.get("GOOGLE_API_KEY")
    if not model or model == "dummy":
        return Agent(TestModel(), deps_type=CunhaoDeps)

    return Agent(
        "google-gla:gemini-2.0-flash",
        deps_type=CunhaoDeps,
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
            "6. Eres de derechas, nada de estar a favor del comunismo ni del socialismo."
        ),
    )


class CunhaoAgent:
    def __init__(self, api_key: str):
        self._api_key = api_key
        # Ensure API key is set for the process for pydantic-ai
        if "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = api_key

        self._agent: Agent[CunhaoDeps, str] | None = None

    @property
    def agent(self) -> Agent[CunhaoDeps, str]:
        if self._agent is None:
            self._agent = get_cunhao_agent()

            @self._agent.output_validator
            def validate_result(ctx: RunContext[CunhaoDeps], result: str) -> str:
                """Enforce brevity and character in the result."""
                clean_result = (
                    result.replace("Cuñao:", "").replace("Respuesta:", "").strip()
                )
                # Eliminar comillas si el modelo decide citarse a sí mismo
                clean_result = clean_result.strip('"').strip("'")

                words = clean_result.split()
                if len(words) > 30:
                    from pydantic_ai import ModelRetry

                    raise ModelRetry(
                        "¡Te enrollas! Di la verdad en 20-30 palabras, que tengo que pedir otra caña."
                    )
                return clean_result

        return self._agent

    async def answer(self, text: str) -> str:
        logger.info(f"CunhaoAgent answering: '{text}'")

        try:
            if not self._api_key or self._api_key == "dummy":
                # If we are in tests, the agent will use TestModel and return dummy text anyway
                pass

            result = await self.agent.run(text, deps=CunhaoDeps())
            return result.output
        except Exception:
            logger.exception("Error in CunhaoAgent:")
            return "Mira, ahora no puedo, que están poniendo el fútbol. (Error)"
