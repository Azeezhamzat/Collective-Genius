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
            name='DelegationRound',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('is_open', models.BooleanField(default=True, help_text='Results are hidden from participants while a round is open, to avoid influencing later votes and delegations.', verbose_name='Open for voting/delegating')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegation_rounds', to='a4modules.module')),
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
                ('delegation_round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='a4_candy_delegation.delegationround')),
            ],
            options={
                'ordering': ('weight', 'id'),
            },
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modified', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegation_votes', to=settings.AUTH_USER_MODEL)),
                ('delegation_round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='a4_candy_delegation.delegationround')),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='a4_candy_delegation.option')),
            ],
            options={
                'unique_together': {('delegation_round', 'creator')},
            },
        ),
        migrations.CreateModel(
            name='Delegation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('delegatee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegations_received', to=settings.AUTH_USER_MODEL)),
                ('delegation_round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegations', to='a4_candy_delegation.delegationround')),
                ('delegator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delegations_given', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('delegation_round', 'delegator')},
            },
        ),
    ]
