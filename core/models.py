import json
import random
import string
from pathlib import Path

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver


def default_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_url = models.URLField(blank=True, default='')


class MonsterCard(models.Model):
    STAGES = [('base', 'Base'), ('fusion', 'Fusión'), ('evolution', 'Evolución')]
    family = models.CharField(max_length=40, db_index=True)
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    stage = models.CharField(max_length=20, choices=STAGES)
    level_min = models.PositiveIntegerField(default=1)
    level_max = models.PositiveIntegerField(default=1)
    hp = models.PositiveIntegerField()
    shell = models.PositiveIntegerField(default=0)
    action_points = models.PositiveIntegerField(default=1)
    movement_points = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True, default='')
    image = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['family', 'stage', 'name']

    def __str__(self):
        return self.name


class Deck(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='decks')
    name = models.CharField(max_length=60)
    cards = models.ManyToManyField(MonsterCard, through='DeckEntry', related_name='decks')
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}: {self.name}"


class DeckEntry(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='entries')
    card = models.ForeignKey(MonsterCard, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('deck', 'card')


class MatchRecord(models.Model):
    room_code = models.CharField(max_length=16, db_index=True, default=default_room_code, unique=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_matches')
    guest = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='guest_matches')
    status = models.CharField(max_length=20, default='waiting')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_matches')
    game_state = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


def _slugify(value: str) -> str:
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = ''.join(ch.lower() if ch.isalnum() else '-' for ch in value)
    value = '-'.join(part for part in value.split('-') if part)
    return value[:140]


@receiver(post_migrate)
def seed_cards(sender, **kwargs):
    if sender.name != 'core':
        return
    data_path = Path(__file__).resolve().parent.parent / 'data' / 'cards.json'
    if not data_path.exists():
        return
    cards = json.loads(data_path.read_text(encoding='utf-8'))
    for item in cards:
        MonsterCard.objects.update_or_create(
            slug=_slugify(item['name']),
            defaults={
                'family': item['family'],
                'name': item['name'],
                'stage': item['stage'],
                'level_min': item['level_min'],
                'level_max': item['level_max'],
                'hp': item['hp'],
                'shell': item['shell'],
                'action_points': item['action_points'],
                'movement_points': item['movement_points'],
                'description': item['description'],
                'image': item['image'],
            }
        )
