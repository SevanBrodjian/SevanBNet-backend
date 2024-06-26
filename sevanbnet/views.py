from django.shortcuts import get_object_or_404, render
from django.views import generic
from django.http import Http404
from rest_framework import viewsets

from .models import Topic, Project, Association, BlogPost, Publication
from .serializers import BlogPostSerializer, ProjectSerializer


def home(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    # num_projects = Project.objects.all().count()
    # num_associations = Association.objects.all().count()
    # num_topics = Topic.objects.all().count()
    # num_ongoing = Project.objects.filter(ongoing__exact=True).count()

    # context = {
    #     'num_projects': num_projects,
    #     'num_associations': num_associations,
    #     'num_topics': num_topics,
    #     'num_ongoing': num_ongoing,
    # }

    return render(request, 'home.html')#, context=context)


def research(request):
    publications = Publication.objects.all()
    return render(request, 'research.html', {'publications': publications})


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


def blog_post(request, stub):
    stub = stub.replace('0', ':').replace('-', ' ').replace('1', '-')
    blog_post = get_object_or_404(BlogPost, title=stub)
    return render(request, 'blog_post.html', context={'post': blog_post})


def blog(request):
    blog_posts = BlogPost.objects.all().order_by('-published_date')
    return render(request, 'blog.html', {'blog_posts': blog_posts})


class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'slug'