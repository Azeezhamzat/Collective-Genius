from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a4_candy_cms_settings', '0007_rebrand_collective_genius_defaults'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisationsettings',
            name='platform_tagline',
            field=models.CharField(
                blank=True,
                default='Empowering Collective Genius',
                help_text='A short line shown alongside the platform '
                          'name -- currently in the footer and the '
                          'installable-app manifest. Leave blank to '
                          'hide it entirely rather than showing an '
                          'empty line.',
                max_length=60,
                verbose_name='Platform tagline'),
        ),
    ]
