# Generated by Django 4.2.3 on 2023-12-23 18:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0019_alter_project_description"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="publication",
            options={
                "ordering": ["rank", "-publication_date", "-submission_date", "title"]
            },
        ),
        migrations.AddField(
            model_name="publication",
            name="authors_str",
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
        migrations.AddField(
            model_name="publication",
            name="rank",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="author",
            name="association",
            field=models.ManyToManyField(blank=True, to="catalog.association"),
        ),
        migrations.AlterField(
            model_name="project",
            name="association",
            field=models.ManyToManyField(blank=True, to="catalog.association"),
        ),
        migrations.AlterField(
            model_name="project",
            name="topic",
            field=models.ManyToManyField(blank=True, to="catalog.topic"),
        ),
        migrations.AlterField(
            model_name="publication",
            name="association",
            field=models.ManyToManyField(blank=True, to="catalog.association"),
        ),
        migrations.AlterField(
            model_name="publication",
            name="authors",
            field=models.ManyToManyField(blank=True, to="catalog.author"),
        ),
        migrations.AlterField(
            model_name="publication",
            name="topic",
            field=models.ManyToManyField(blank=True, to="catalog.topic"),
        ),
    ]
