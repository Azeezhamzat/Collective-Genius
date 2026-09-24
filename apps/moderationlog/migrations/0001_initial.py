from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('a4projects', '0034_contact_mixin_help_texts'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flag', models.CharField(choices=[('is_censored', 'is_censored'), ('is_removed', 'is_removed'), ('is_blocked', 'is_blocked')], max_length=32)),
                ('action', models.CharField(choices=[('set', 'Set'), ('cleared', 'Cleared')], max_length=16)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moderation_log_entries', to='a4projects.project')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
    ]
