import json
import logging
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS
from django.db.utils import OperationalError, ProgrammingError
from django.utils.text import slugify

from .models import MonsterCard

logger = logging.getLogger(__name__)

CARDS_DATA_PATH = Path(settings.BASE_DIR) / 'data' / 'cards.json'
SUMMON_COST_BY_STAGE = {
    'base': 1,
    'fusion': 3,
    'evolution': 5,
}
OPTIONAL_CARD_DEFAULTS = {
    'description': '',
    'image': '',
    'shell': 0,
    'action_points': 1,
    'movement_points': 1,
}
REQUIRED_CARD_FIELDS = (
    'name',
    'family',
    'stage',
    'level_min',
    'level_max',
    'hp',
)


@dataclass
class CardImportStats:
    processed: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0


def slugify_card_name(value: str) -> str:
    return slugify((value or '').strip(), allow_unicode=False)[:140]


def resolve_card_image(image: str) -> str:
    raw = (image or '').strip()
    if not raw:
        return ''
    if raw.startswith(('http://', 'https://', '/')):
        return raw
    cleaned = raw[7:] if raw.startswith('public/') else raw
    return f'/static/{cleaned}'


def summon_cost(card_like) -> int:
    stage = card_like.get('stage', 'base')
    return SUMMON_COST_BY_STAGE.get(stage, 1)


def serialize_card(card: MonsterCard) -> dict:
    return {
        'id': card.id,
        'name': card.name,
        'slug': card.slug,
        'family': card.family,
        'stage': card.stage,
        'level_min': card.level_min,
        'level_max': card.level_max,
        'hp': card.hp,
        'shell': card.shell,
        'action_points': card.action_points,
        'movement_points': card.movement_points,
        'description': card.description,
        'image': resolve_card_image(card.image),
        'summon_cost': summon_cost({'stage': card.stage}),
    }


def serialized_cards_queryset():
    return [serialize_card(card) for card in MonsterCard.objects.all()]


def load_cards_seed_data(path=CARDS_DATA_PATH):
    if not path.exists():
        logger.warning('Cards seed file not found at %s', path)
        return []
    return json.loads(path.read_text(encoding='utf-8'))


def _normalized_card_payload(item):
    missing_fields = [field for field in REQUIRED_CARD_FIELDS if item.get(field) in (None, '')]
    if missing_fields:
        raise ValueError(f"faltan campos requeridos: {', '.join(missing_fields)}")

    payload = {
        'family': item['family'],
        'name': item['name'],
        'stage': item['stage'],
        'level_min': item['level_min'],
        'level_max': item['level_max'],
        'hp': item['hp'],
        'shell': item.get('shell', OPTIONAL_CARD_DEFAULTS['shell']),
        'action_points': item.get('action_points', OPTIONAL_CARD_DEFAULTS['action_points']),
        'movement_points': item.get('movement_points', OPTIONAL_CARD_DEFAULTS['movement_points']),
        'description': item.get('description', OPTIONAL_CARD_DEFAULTS['description']),
        'image': item.get('image', OPTIONAL_CARD_DEFAULTS['image']),
    }
    slug = slugify_card_name(payload['name'])
    if not slug:
        raise ValueError('no se pudo generar un slug válido')
    return slug, payload


def import_monster_cards(*, using=DEFAULT_DB_ALIAS, path=CARDS_DATA_PATH, stdout=None):
    stats = CardImportStats()

    try:
        MonsterCard.objects.using(using).exists()
    except (ProgrammingError, OperationalError):
        return stats

    for index, item in enumerate(load_cards_seed_data(path=path), start=1):
        try:
            slug, defaults = _normalized_card_payload(item)
        except ValueError as exc:
            stats.skipped += 1
            if stdout:
                stdout.write(f"[WARN] Carta #{index} omitida: {exc}.")
            continue

        stats.processed += 1
        card, created = MonsterCard.objects.using(using).update_or_create(
            slug=slug,
            defaults=defaults,
        )
        if created:
            stats.created += 1
            if stdout:
                stdout.write(f"[CREATE] {card.name} ({card.slug})")
            continue

        stats.updated += 1
        if stdout:
            stdout.write(f"[UPDATE] {card.name} ({card.slug})")

    return stats
