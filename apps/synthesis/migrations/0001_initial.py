from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('a4modules', '0005_module_is_draft'),
        ('a4comments', '0009_comment_is_blocked'),
    ]

    operations = [
        migrations.CreateModel(
            name='SynthesisSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('n_participants', models.PositiveIntegerField(default=0)),
                ('n_statements', models.PositiveIntegerField(default=0)),
                ('n_groups', models.PositiveIntegerField(default=0)),
                ('group_sizes', models.JSONField(blank=True, default=dict)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='synthesis_snapshots', to='a4modules.module')),
            ],
            options={
                'ordering': ('-created',),
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='StatementResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n_votes', models.PositiveIntegerField()),
                ('agree_ratio', models.FloatField()),
                ('consensus_score', models.FloatField()),
                ('divisiveness', models.FloatField()),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='synthesis_results', to='a4comments.comment')),
                ('snapshot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statement_results', to='a4_candy_synthesis.synthesissnapshot')),
            ],
            options={
                'ordering': ('-consensus_score',),
            },
        ),
    ]
