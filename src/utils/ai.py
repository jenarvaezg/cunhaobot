import os
from google import genai
from typing import List


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    return genai.Client(api_key=api_key)


async def generate_cunhao_phrases(count: int = 5) -> List[str]:
    """Generates cuñao-style phrases using Gemini."""
    client = get_client()

    prompt = f"""
    Actúa como un "cuñao" español de manual en una barra de bar.
    Genera {count} frases lapidarias, cortas y directas.

    REGLAS CRÍTICAS:
    1. CADA FRASE DEBE TENER UNA SOLA IDEA O CONCEPTO (No mezcles temas).
    2. BREVEDAD: Máximo 15-20 palabras por frase. Que sean "perlas" rápidas.
    3. TONO: Sentando cátedra, rancio, nostálgico, escéptico y políticamente incorrecto.

    Tópicos de ejemplo (elige uno distinto por frase):
    - Odio al lenguaje inclusivo o "moderneces".
    - El coche diésel/manual es lo único que vale.
    - La mili te hacía hombre.
    - El cambio climático es mentira porque hoy hace frío.
    - El chuletón/jamón cura cualquier tontería.
    - Los jóvenes no quieren trabajar.
    - Nacionalismo rancio o prejuicios sobre inmigración/paguitas.
    - Machismo rancio.

    IMPORTANTE: Devuelve SOLO las frases, una por línea, sin numeración ni explicaciones.
    """

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview", contents=prompt
        )

        phrases = [
            line.strip() for line in response.text.strip().split("\n") if line.strip()
        ]
        return phrases[:count]
    except Exception as e:
        if "429" in str(e):
            return [
                "⚠️ Quota de AI agotada. ¡Paco no puede más con el calor! Reintenta en un momento."
            ]
        raise e
