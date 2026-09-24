from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('a4_candy_documents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParagraphRevision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('paragraph', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='revisions', to='a4_candy_documents.paragraph')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
    ]
