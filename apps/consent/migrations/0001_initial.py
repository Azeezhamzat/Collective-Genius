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
            name='Proposal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('description', models.TextField(verbose_name='Description')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consent_proposals', to=settings.AUTH_USER_MODEL)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consent_proposals', to='a4modules.module')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stance', models.CharField(choices=[('agree', 'Agree'), ('stand_aside', "Stand aside (won't block, doesn't support)"), ('object', 'Object (blocks the proposal until resolved)')], max_length=16)),
                ('reason', models.TextField(blank=True, help_text='Required for an objection -- what would need to change for you to withdraw it?', verbose_name='Reason')),
                ('resolved', models.BooleanField(default=False, help_text='Only meaningful for an objection: has it been addressed? The proposer (or the objector themselves) can mark it resolved once it no longer stands in the way.', verbose_name='Resolved')),
                ('modified', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consent_responses', to=settings.AUTH_USER_MODEL)),
                ('proposal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='a4_candy_consent.proposal')),
            ],
            options={
                'unique_together': {('proposal', 'creator')},
            },
        ),
    ]
