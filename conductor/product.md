# Product Guide: cunhaobot

## Initial Concept
A multi-platform chatbot (Telegram, Slack, Twitter) designed to simulate a "cuñado" (brother-in-law) persona: opinionated, humorous, and engaging. The bot currently offers conversational AI, sticker management, and a community ranking system. The next major phase is the integration of "Arena de Tasca," an asynchronous auto-battler game.

## Core Value Proposition
*   **Humor:** Delivers entertainment through a culturally specific, humorous persona.
*   **Community:** Foster engagement through rankings, badges, and now, competitive gameplay.
*   **Multi-platform:** accessible where the conversation happens.

## "Arena de Tasca" (Game Module)
A "MyBrute" style auto-battler where users manage a "Fighter" avatar that battles others automatically based on stats and RNG.

### Key Features
1.  **Character Creation:**
    *   **Name:** Inherited from user or custom (e.g., "Paco 'El Grifo'").
    *   **Stats (The 4 Pillars):**
        *   **Vozarrón (Strength):** Damage output.
        *   **Cintura (Agility):** Dodge/Block chance.
        *   **Verborrea (Speed):** Initiative and combo chance.
        *   **Aguante (HP):** Health points.
    *   **Inventory:** Weapons (Palillo, Servilleta, etc.) and Skills (active/passive).

2.  **Combat System:**
    *   **Asynchronous:** Users do not need to be online simultaneously.
    *   **Automatic:** Server-side simulation based on logic and RNG.
    *   **Visualization:** Text-based battle logs initially, evolving to a web-based visual replay.
    *   **Environment:** Different "Bar" locations that provide buffs/debuffs or trigger random events (e.g., "Free Tapas" heals HP).

3.  **Progression:**
    *   **Leveling:** XP gained from fights (winner gets more).
    *   **Choices:** At each level up, the user MUST choose between two random upgrades (e.g., "+3 Vozarrón" OR "New Skill: Golpe de Remo").
    *   **Leagues:** Unlock new bar locations by winning fights in the current tier.

4.  **Integration:**
    *   Uses existing bot currency/points for utility actions (healing fatigue, cosmetic changes).
    *   Commands: `/arena crear`, `/duelo @user`, `/perfil`.

## Target Audience
*   Spanish-speaking users familiar with the "cuñado" trope.
*   Telegram and Slack communities looking for lightweight, interactive entertainment.
