"""Papers get their own Code link. Until now the Papers page took a paper's code from its
linked project's Source, so papers without an on-site project could have none. Each paper
linked to a project starts with that project's Source (when it is a web link), so every
Code button showing today still shows."""

from django.db import migrations, models


def copy_project_source(apps, schema_editor):
    Publication = apps.get_model("sevanbnet", "Publication")
    for paper in Publication.objects.filter(code_url="").exclude(project=None):
        source = paper.project.source
        if source.startswith(("https://", "http://")):
            paper.code_url = source
            paper.save(update_fields=["code_url"])


class Migration(migrations.Migration):
    dependencies = [
        ("sevanbnet", "0034_project_standalone"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="code_url",
            field=models.URLField(
                blank=True,
                help_text="The paper's code, e.g. its GitHub repository. Shows a Code button on "
                "the Papers page.",
                max_length=500,
                verbose_name="Code link",
            ),
        ),
        migrations.RunPython(copy_project_source, migrations.RunPython.noop),
    ]
