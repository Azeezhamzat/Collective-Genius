import django.db.models.deletion
from django.db import migrations, models

import apps.webhooks.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('a4_candy_organisations',
         '0018_add_kyrgyz_and_russian_language_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='Endpoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(verbose_name='Endpoint URL')),
                ('secret', models.CharField(default=apps.webhooks.models._generate_secret, editable=False, help_text='Used to sign delivered payloads (HMAC-SHA256, hex-encoded, sent as the X-Webhook-Signature header) so the receiver can verify a delivery really came from here.', max_length=64)),
                ('event_types', models.JSONField(blank=True, default=list, help_text='Which events to send. Empty means every event type.', verbose_name='Event types')),
                ('is_active', models.BooleanField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhook_endpoints', to='a4_candy_organisations.organisation')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(max_length=100)),
                ('data', models.JSONField()),
                ('attempt_number', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed (retries exhausted)')], default='pending', max_length=16)),
                ('response_status', models.PositiveIntegerField(blank=True, null=True)),
                ('error', models.TextField(blank=True)),
                ('next_retry_at', models.DateTimeField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('endpoint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='a4_candy_webhooks.endpoint')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
    ]
