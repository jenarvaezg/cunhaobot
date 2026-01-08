# Product Guidelines: cunhaobot

## 1. Tone and Voice
The bot maintains a consistent **"Cuñado" Persona** across all interactions (text, audio, error messages).

*   **Personality:** Overconfident, loud, affectionate but condescending ("fiera", "maquina", "campeón"), and opinionated. He knows everything, even when he's wrong.
*   **Language:**
    *   **Informal Spanish:** Heavy use of slang from Spain.
    *   **Clichés:** Use established phrases like "tú hazme caso a mí", "esto con Franco no pasaba" (careful with politics, keep it satirical), "yo de esto piloto".
    *   **Directness:** Never apologize for errors; blame the system, the government, or the user's "lack of culture."

## 2. Visual Identity
*   **Aesthetic:** "Bar de Tasca" (Old-school Spanish Tavern).
*   **Elements:** Wooden textures, napkins, toothpicks, beer/wine, football references.
*   **UI/Web:** Simple, functional, slightly retro. Avoid overly polished "tech startup" looks; it should feel "homemade" but robust.

## 3. Game Design Philosophy
*   **Casual & accessible:** Games are "second screen" experiences or quick distractions (5-30 seconds).
*   **RNG as Logic:** Randomness simulates the chaotic nature of "cuñado" logic. Luck is a skill.
*   **Grind & Glory:** Reward persistence over skill. The user who spends the most time (or "talks the loudest") wins.

## 4. Multi-platform Strategy
*   **Feature Parity:** Strive for consistent experience across Telegram and Slack, but adapt UI to platform constraints (e.g., Telegram Web Apps vs. Slack Modals).
*   **Identity First:** The user is the same person regardless of the platform. The `User` entity and `/link` command are central to this unification.
