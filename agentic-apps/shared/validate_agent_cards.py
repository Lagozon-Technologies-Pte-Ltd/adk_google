import json
from pathlib import Path

from jsonschema import Draft202012Validator


BASE_DIR = Path(__file__).resolve().parents[1]
CARDS_DIR = BASE_DIR / "agent_cards"
SCHEMA_PATH = BASE_DIR / "schemas" / "agent_card.schema.json"


class AgentCardValidationError(RuntimeError):
    pass


def load_schema() -> dict:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_all_agent_cards() -> dict[str, dict]:
    """
    Validates all AgentCards.
    Returns dict[name -> card]
    Raises AgentCardValidationError on failure.
    """
    schema = load_schema()
    validator = Draft202012Validator(schema)

    cards = {}

    for card_file in CARDS_DIR.glob("*.json"):
        with open(card_file, "r", encoding="utf-8") as f:
            card = json.load(f)

        errors = sorted(validator.iter_errors(card), key=lambda e: e.path)
        if errors:
            error_messages = []
            for err in errors:
                location = ".".join(map(str, err.path)) or "root"
                error_messages.append(f"{location}: {err.message}")

            raise AgentCardValidationError(
                f"\n❌ Invalid AgentCard: {card_file.name}\n"
                + "\n".join(error_messages)
            )

        cards[card["name"]] = card

    if not cards:
        raise AgentCardValidationError("No AgentCards found.")

    return cards
