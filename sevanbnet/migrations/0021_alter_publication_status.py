# Generated by Django 4.2.3 on 2024-01-06 01:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sevanbnet", "0020_alter_publication_options_publication_authors_str_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publication",
            name="status",
            field=models.CharField(max_length=1000),
        ),
    ]
