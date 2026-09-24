from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a4_candy_cms_settings', '0006_add_helptexts_to_organisation_pages'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organisationsettings',
            name='platform_name',
            field=models.CharField(default='Collective Genius', max_length=20, verbose_name='Platform name', help_text='This name appears in the footer of all pages and e-mails as well as in the tab of the browser.'),
        ),
        migrations.AlterField(
            model_name='socialmedia',
            name='fallback_description_de',
            field=models.TextField(default='Collective Genius macht kollektive Intelligenz einfach – für jede Gruppe, überall.'),
        ),
        migrations.AlterField(
            model_name='socialmedia',
            name='fallback_description_en',
            field=models.TextField(default='Collective Genius makes collective intelligence easy - for any group, anywhere.'),
        ),
    ]
