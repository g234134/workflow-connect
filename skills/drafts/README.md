# Skill Card drafts (`skills/drafts/`)

Semi-automatic drafts from `04_Workflows/_wave8_generate_skill_card_draft.py` land here as `*.json` until a human promotes or rejects them via `04_Workflows/_wave8_skill_card_review_queue.py`.

- **Promoted** → `skills/cards/` (`approve`)
- **Rejected** → `skills/rejected/` (`reject`)

Drafts are **not** loaded by the Skill Registry selector until approved and placed under `skills/cards/`.
