from django.contrib import admin
from .models import Deck, DeckEntry, MatchRecord, MonsterCard, UserProfile

admin.site.register(UserProfile)
admin.site.register(MonsterCard)
admin.site.register(Deck)
admin.site.register(DeckEntry)
admin.site.register(MatchRecord)
