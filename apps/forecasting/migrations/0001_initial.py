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
                ('resolution_criteria', models.TextField(blank=True, help_text='How will it be decided, objectively, whether this resolves yes or no? Vague criteria make the forecasts meaningless.', verbose_name='Resolution criteria')),
                ('closes_at', models.DateTimeField(blank=True, help_text='After this date, forecasts can no longer be submitted or changed. Leave blank to allow forecasts until resolution.', null=True, verbose_name='Forecasting closes at')),
                ('is_resolved', models.BooleanField(default=False, verbose_name='Resolved')),
                ('outcome', models.BooleanField(blank=True, help_text='Only meaningful once resolved: did it happen?', null=True, verbose_name='Outcome')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forecasting_questions', to='a4modules.module')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Forecast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('probability', models.PositiveSmallIntegerField(verbose_name='Probability (%)')),
                ('modified', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forecasts', to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forecasts', to='a4_candy_forecasting.question')),
            ],
            options={
                'unique_together': {('question', 'creator')},
            },
        ),
    ]
