# Generated by Django 4.2 on 2023-04-10 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sevanbnet", "0008_alter_project_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="img",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
