# Generated by Django 4.2.3 on 2024-05-31 21:43

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("sevanbnet", "0023_blogpost_slug"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="project",
            options={"ordering": ["-end", "title"]},
        ),
        migrations.RemoveField(
            model_name="blogpost",
            name="image",
        ),
        migrations.RemoveField(
            model_name="project",
            name="ongoing",
        ),
        migrations.RemoveField(
            model_name="publication",
            name="authors",
        ),
        migrations.AlterField(
            model_name="blogpost",
            name="published_date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.DeleteModel(
            name="Author",
        ),
    ]
