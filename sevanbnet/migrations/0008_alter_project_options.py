# Generated by Django 4.1.4 on 2022-12-29 23:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sevanbnet", "0007_remove_project_topic_project_topic"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="project", options={"ordering": ["-ongoing", "-end", "title"]},
        ),
    ]
