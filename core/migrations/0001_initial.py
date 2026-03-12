from django.db import migrations, models
import django.db.models.deletion
import core.models
from django.conf import settings

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name='MonsterCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('family', models.CharField(db_index=True, max_length=40)),
                ('name', models.CharField(max_length=120, unique=True)),
                ('slug', models.SlugField(max_length=140, unique=True)),
                ('stage', models.CharField(choices=[('base', 'Base'), ('fusion', 'Fusión'), ('evolution', 'Evolución')], max_length=20)),
                ('level_min', models.PositiveIntegerField(default=1)),
                ('level_max', models.PositiveIntegerField(default=1)),
                ('hp', models.PositiveIntegerField()),
                ('shell', models.PositiveIntegerField(default=0)),
                ('action_points', models.PositiveIntegerField(default=1)),
                ('movement_points', models.PositiveIntegerField(default=1)),
                ('description', models.TextField(blank=True, default='')),
                ('image', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['family', 'stage', 'name']},
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar_url', models.URLField(blank=True, default='')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Deck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decks', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-updated_at']},
        ),
        migrations.CreateModel(
            name='MatchRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_code', models.CharField(db_index=True, default=core.models.default_room_code, max_length=16, unique=True)),
                ('status', models.CharField(default='waiting', max_length=20)),
                ('game_state', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='guest_matches', to=settings.AUTH_USER_MODEL)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hosted_matches', to=settings.AUTH_USER_MODEL)),
                ('winner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='won_matches', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-updated_at']},
        ),
        migrations.CreateModel(
            name='DeckEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.monstercard')),
                ('deck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='core.deck')),
            ],
        ),
        migrations.AddField(
            model_name='deck',
            name='cards',
            field=models.ManyToManyField(related_name='decks', through='core.DeckEntry', to='core.monstercard'),
        ),
        migrations.AlterUniqueTogether(name='deckentry', unique_together={('deck', 'card')}),
    ]
