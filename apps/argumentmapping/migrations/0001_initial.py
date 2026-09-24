from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('a4comments', '0009_comment_is_blocked'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(choices=[('supports', 'Supports'), ('opposes', 'Opposes')], max_length=16)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('comment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stance', to='a4comments.comment')),
            ],
        ),
    ]
