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
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Question')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('scale_hint', models.CharField(blank=True, help_text='What unit is the estimate in? e.g. "0-100", "years", "EUR". Shown next to the input field.', max_length=64, verbose_name='Scale')),
                ('current_round', models.PositiveIntegerField(default=1)),
                ('is_closed', models.BooleanField(default=False, help_text='No more rounds will open once closed.', verbose_name='Closed')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delphi_questions', to='a4modules.module')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_number', models.PositiveIntegerField()),
                ('value', models.FloatField(verbose_name='Your estimate')),
                ('rationale', models.TextField(blank=True, help_text='Why this estimate? Shown anonymously alongside the aggregate in the next round.', verbose_name='Rationale (optional)')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delphi_responses', to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='a4_candy_delphi.question')),
            ],
            options={
                'ordering': ('round_number', 'id'),
                'unique_together': {('question', 'round_number', 'creator')},
            },
        ),
    ]
