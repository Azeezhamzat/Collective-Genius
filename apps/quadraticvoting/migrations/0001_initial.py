from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('a4modules', '0005_module_is_draft'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VotingRound',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('credit_budget', models.PositiveIntegerField(default=100, help_text='How many credits each participant can spend in total across all options. Casting N votes on one option costs N*N credits.', verbose_name='Voice credit budget')),
                ('is_open', models.BooleanField(default=True, help_text='Results are hidden from participants while a round is open, to avoid influencing later votes.', verbose_name='Open for voting')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quadratic_voting_rounds', to='a4modules.module')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('weight', models.PositiveIntegerField(default=0)),
                ('voting_round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='a4_candy_quadraticvoting.votinground')),
            ],
            options={
                'ordering': ('weight', 'id'),
            },
        ),
        migrations.CreateModel(
            name='Allocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('votes', models.IntegerField(default=0)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quadratic_vote_allocations', to=settings.AUTH_USER_MODEL)),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='allocations', to='a4_candy_quadraticvoting.option')),
            ],
            options={
                'unique_together': {('option', 'creator')},
            },
        ),
    ]
