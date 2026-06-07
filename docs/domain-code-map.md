# Domain To Code Map

This document maps Spanish domain language from `CONTEXT.md` to current English code identifiers.

The glossary is authoritative for product language. Code identifiers remain English. Some code names are historical and do not yet match the domain precisely.

| Domain term | Current code identifiers | Notes |
| --- | --- | --- |
| **Apelativo** | `Phrase`, `PhraseRepository`, `phrase_repo`, short inline mode | Historical name: the project originally only stored short greeting words and called them phrases. |
| **Frase cuñadil** | `LongPhrase`, `LongPhraseRepository`, `long_phrase_repo`, long inline mode | Historical name: added later as "long phrase" to distinguish it from `Phrase`. |
| **Pieza cuñadil** | Currently `Phrase` and `LongPhrase`; future approved content models | Umbrella domain term for approved repertory content. |
| **Cuenta de plataforma** | `User` records with `platform`, platform-specific IDs | A Telegram or Slack identity before conceptual unification into a profile. |
| **Perfil** | The canonical `User` record reached after account linking; `linked_to` marks absorbed platform accounts | The domain term is "Perfil", but code should keep English names. |
| **Chat** | `Chat`, `ChatRepository`, `chat_repo` | The conversation space where the bot participates; currently also carries chat-level state. |
| **Suscripción Premium** | `Chat.premium_until`, `/premium`, `ActionType.SUBSCRIPTION` | Premium is currently chat-scoped, not profile-scoped. |
| **Propuesta** | `Proposal`, `LongProposal`, `ProposalService`, `proposal_repo`, `long_proposal_repo` | Current code has separate proposal classes for historical apelativo/frase split. |
| **Consejo** | `config.mod_chat_id`, Telegram chat administrators, `get_curators`, approve/reject callbacks | Domain term for the people who evaluate proposals. |
| **Logro** | `Badge`, `BadgeProgress`, `BADGES`, `User.badges`, `BadgeService` | Code uses badge terminology; domain language should say "Logro". |
| **Puntos de reputación** | `User.points`, `add_points` | General prestige balance for a profile. |
| **Juego** | `GameController`, `GameService`, `/game`, `palillo_cunhao`, `/jugar` | Current production game is Palillo, but the domain term stays generic. |
| **Partida** | score submission flow, `GameService.set_score` | Current code records aggregate game stats rather than a separate persisted play record. |
| **Puntuación de partida** | `score`, `User.game_high_score`, `GameService.set_score` | Game result; code may convert it into reputation points. |
| **Clasificación de reputación** | `/ranking`, `WebController.ranking`, `ranking.html` | Ordered by `User.points`. |
| **Clasificación de juego** | `/game/ranking`, `/top_jugones`, `game_ranking.html`, `handle_top_jugones` | Ordered by `User.game_high_score`. |
| **Regalo** | `Gift`, `GiftType`, `GiftRepository`, `/regalar`, gift payment payloads | Social digital gift between profiles in a chat. |
| **Póster** | `PosterRequest`, `PosterRequestRepository`, `/poster`, `AIService.generate_image` | On-demand generated image, not approved repertory content. |

## Naming Rule

- Domain documentation uses Spanish product terms from `CONTEXT.md`.
- Python code, tests, modules, functions, classes, and variables use English identifiers.
- When changing code near a historical name, prefer clearer English names for new symbols while preserving compatibility with existing persisted data.

## Deepened Module Interfaces

These modules hide historical implementation details behind a small, stable interface. Callers cross the interface instead of reassembling behavior.

| Domain concern | Deeper interface | What it hides |
| --- | --- | --- |
| **Partida** submission | `GameService.submit_score()` | Token validation, high-score/streak update, single Puntuación → Puntos de reputación conversion. |
| **Pieza cuñadil** intake | `ProposalService.submit()` → `IntakeResult` | Empty/duplicate decision across approved Pieza cuñadil and pending/rejected Propuesta; Apelativo vs Frase cuñadil split (derived from proposal type). |
| Paid fulfillment | `services.payment.parse_payment_payload()` → `GiftPayment` / `SubscriptionPayment` / `PosterPayment` | `startswith`/`split` parsing; routing to Regalo, Póster or Suscripción Premium. |
| **Perfil** linking | `UserService.complete_link()` / `_migrate_authorship()` | Token lifecycle, canonical resolution, absorbed-account aliasing, one-seam authorship migration. |
| **Logro** engine | `BadgeService.check_badges()` → `list[Badge]` | Milestone rules; platform notification stays in Telegram/Slack adapters. |
| **Perfil** aggregation | `ProfileService.get_profile_summary()` → `ProfileSummary` | One coherent summary (Puntos, Logros, Pieza cuñadil, Regalos, Pósters) for web and bot. |
| **Chat** interaction | `ChatInteractionService` (`answer`, `decide_reaction`, `record_reaction_received`) | Shared AI response, reaction decision and Uso logging across Telegram and Slack adapters. |
| Composition | `core.container.Container` | Single composition root; `core.di` only exposes its singletons to Litestar. |
