from sevanbnet.models import Project
from django.utils.text import slugify

projects = Project.objects.all()
for project in projects:
    if not project.slug:
        project.slug = slugify(project.title)
        project.save()
