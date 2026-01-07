# Specification: Arena de Tasca Core Backend

## Context
"Arena de Tasca" is a new asynchronous auto-battler game mode for `cunhaobot`. This track focuses on building the foundational backend components required to persist game state and simulate battles. We need to define the data models for Fighters and Fights and implement the service layer that handles the game logic (combat simulation, leveling, stats).

## Requirements

### 1. Data Models (Infrastructure/Datastore)
*   **`Fighter` Model:**
    *   Must be linked to a unique `User`.
    *   **Attributes:**
        *   `user_id` (Integer, Indexed)
        *   `name` (String)
        *   `level` (Integer, default 1)
        *   `xp` (Integer, default 0)
        *   **Stats:** `vozarron` (Strength), `cintura` (Agility), `verborrea` (Speed), `aguante` (HP).
        *   `wins` (Integer), `losses` (Integer).
        *   `last_fight_at` (Datetime, for fatigue management).
    *   **Methods:** `to_dict`, `from_entity` (standard Datastore patterns).

*   **`Fight` Model:**
    *   Represents a single combat instance.
    *   **Attributes:**
        *   `id` (String/UUID)
        *   `fighter_a_id` (Integer)
        *   `fighter_b_id` (Integer)
        *   `winner_id` (Integer)
        *   `log` (JSON/List of dictionaries describing the turns).
        *   `created_at` (Datetime).

### 2. Service Layer (`ArenaService`)
*   **Initialization:**
    *   `create_fighter(user_id, name)`: Creates a new fighter with base stats.
    *   `get_fighter(user_id)`: Retrieves a user's fighter.
*   **Matchmaking:**
    *   `find_opponent(fighter)`: logic to find a suitable opponent (e.g., similar level).
*   **Combat Engine:**
    *   `simulate_fight(fighter_a, fighter_b)`:
        *   Calculates initiative.
        *   Loops through turns until one fighter's HP <= 0.
        *   Applies damage formulas based on `Vozarrón` vs `Cintura`.
        *   Generates a structured `battle_log`.
    *   **Formulas (Draft):**
        *   *Hit Chance:* Base 80% + (Verborrea_A - Cintura_B * 2).
        *   *Damage:* Vozarrón_A * Random(0.8, 1.2).
        *   *Crit Chance:* Based on Verborrea.
*   **Progression:**
    *   `award_xp(fighter, amount)`: Updates XP and handles leveling up checks.

### 3. Integration
*   Ensure models follow the existing `src/models/` and `src/infrastructure/datastore/` patterns.
*   Use `pydantic` v2 for domain models.
*   Use dependency injection for the repository layer.

## Technical Constraints
*   **Database:** Google Cloud Datastore.
*   **Language:** Python 3.14.
*   **Testing:** 80% coverage required. Use `pytest`.
*   **Type Safety:** Strict typing with `ty` (no `Any` without explicit reason).

## Out of Scope
*   Web UI / Visual Replay (Fase 2).
*   Telegram Commands (will be added in the next track).
*   Inventory/Weapon system (simplified for now to just base stats).
