from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a4_candy_organisations',
         '0018_add_kyrgyz_and_russian_language_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='custom_css',
            field=models.TextField(
                blank=True,
                help_text="Plain CSS, inserted into every page on this "
                          "organisation's platform inside a <style> tag "
                          "scoped after the default stylesheet. Use it to "
                          're-theme colors, fonts and spacing for a '
                          'white-labelled deployment, e.g. ".btn--primary '
                          '{ background-color: #123456; }". Only '
                          'organisation initiators can set this -- the '
                          'same trust level as the imprint and other '
                          'rich-text fields below, which already allow '
                          'arbitrary HTML.',
                verbose_name='Custom CSS'),
        ),
    ]
