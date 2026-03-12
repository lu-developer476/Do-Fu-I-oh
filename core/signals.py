import json
from pathlib import Path

from django.conf import settings

from .models import MonsterCard


def seed_cards(sender, **kwargs):
    data_file = Path(settings.BASE_DIR) / "data" / "cards.json"

    if not data_file.exists():
        return

    with open(data_file, "r", encoding="utf-8") as f:
        cards = json.load(f)

    for card in cards:
        MonsterCard.objects.update_or_create(
            slug=card["slug"],
            defaults={
                "name": card["name"],
                "family": card["family"],
                "stage": card["stage"],
                "level": card["level"],
                "hp": card["hp"],
                "shell_points": card["shell_points"],
                "action_points": card["action_points"],
                "movement_points": card["movement_points"],
                "description": card.get("description", ""),
                "image": card.get("image", ""),
            },
        )
