# Plan: Arena de Tasca Core Backend

## Phase 1: Data Models & Persistence

- [ ] Task: Create Pydantic Domain Models
    - [ ] Subtask: Write tests for `Fighter` and `Fight` domain models in `src/models/arena_test.py`.
    - [ ] Subtask: Implement `Fighter` and `Fight` Pydantic models in `src/models/arena.py` following project standards.
    - [ ] Subtask: Verify tests pass.

- [ ] Task: Create Datastore Repository
    - [ ] Subtask: Write integration tests for `ArenaRepository` in `src/infrastructure/datastore/arena_test.py` (mocking Datastore client).
    - [ ] Subtask: Implement `ArenaRepository` in `src/infrastructure/datastore/arena.py` handling CRUD for Fighters and Fights.
    - [ ] Subtask: Register new repository in `src/core/container.py` (DI container).
    - [ ] Subtask: Verify tests pass.

- [ ] Task: Conductor - User Manual Verification 'Data Models & Persistence' (Protocol in workflow.md)

## Phase 2: Arena Service & Combat Logic

- [ ] Task: Implement Fighter Management Logic
    - [ ] Subtask: Write tests for `create_fighter` and `get_fighter` in `src/services/arena_service_test.py`.
    - [ ] Subtask: Create `ArenaService` class in `src/services/arena_service.py` and implement management methods.
    - [ ] Subtask: Verify tests pass.

- [ ] Task: Implement Combat Engine (Simulation)
    - [ ] Subtask: Write tests for `simulate_fight` covering win/loss, crit logic, and turn limits.
    - [ ] Subtask: Implement `simulate_fight` method in `ArenaService`.
        -   Define initiative logic.
        -   Define damage/hit formulas.
        -   Generate structured battle logs.
    - [ ] Subtask: Verify tests pass.

- [ ] Task: Conductor - User Manual Verification 'Arena Service & Combat Logic' (Protocol in workflow.md)

## Phase 3: Progression & Matchmaking

- [ ] Task: Implement XP and Leveling
    - [ ] Subtask: Write tests for `award_xp` verifying level-up thresholds.
    - [ ] Subtask: Implement `award_xp` logic in `ArenaService`.
    - [ ] Subtask: Verify tests pass.

- [ ] Task: Implement Basic Matchmaking
    - [ ] Subtask: Write tests for `find_opponent`.
    - [ ] Subtask: Implement `find_opponent` in `ArenaService` (fetching random fighter of similar level).
    - [ ] Subtask: Verify tests pass.

- [ ] Task: Conductor - User Manual Verification 'Progression & Matchmaking' (Protocol in workflow.md)
