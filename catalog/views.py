from django.shortcuts import render
from django.views import generic
from django.http import Http404

from .models import Topic, Project, Association


def home(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_projects = Project.objects.all().count()
    num_associations = Association.objects.all().count()
    num_topics = Topic.objects.all().count()
    num_ongoing = Project.objects.filter(ongoing__exact=True).count()

    context = {
        'num_projects': num_projects,
        'num_associations': num_associations,
        'num_topics': num_topics,
        'num_ongoing': num_ongoing,
    }

    return render(request, 'home.html', context=context)

def resume(request):
    return render(request, 'resume.html', {})

def contact(request):
    return render(request, 'contact.html', {})

class ProjectListView(generic.ListView):
    model = Project
    context_object_name = 'projects'
    template_name = 'projects.html'
    paginate_by = 10


def project_detail_view(request, stub):
    stub=stub.replace('_', ' ')
    try:
        project = Project.objects.get(title=stub)
    except Project.DoesNotExist:
        raise Http404('Project does not exist')

    topics = ""
    first = True
    for topic in project.topic.all():
        if first:
            topics += topic.name
            first = False
        else:
            topics += ", " + topic.name

    return render(request, 'project_detail.html', context={'project': project, 'topics': topics})

# class ProjectDetailView(generic.DetailView):
#     model = Project
#     context_object_name = 'project'
#     template_name = 'project_detail.html'

#     def get_object(queryset=None):
#         print(queryset)