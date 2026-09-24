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
            name='SummarySnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('n_comments', models.PositiveIntegerField(default=0)),
                ('keywords', models.JSONField(blank=True, default=list)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='summary_snapshots', to='a4modules.module')),
            ],
            options={
                'ordering': ('-created',),
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='KeyComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField()),
                ('rank', models.PositiveIntegerField()),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='summary_appearances', to='a4comments.comment')),
                ('snapshot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='key_comments', to='a4_candy_summarization.summarysnapshot')),
            ],
            options={
                'ordering': ('rank',),
            },
        ),
    ]
