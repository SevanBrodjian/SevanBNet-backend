# Generated by Django 4.2.3 on 2023-09-20 00:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sevanbnet', '0010_blogpost'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blogpost',
            options={'ordering': ['published_date']},
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='image',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
