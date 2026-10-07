from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from rest_framework import viewsets

from .models import BlogPost, Project, Publication
from .serializers import BlogPostSerializer, ProjectSerializer, PublicationSerializer


class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlogPost.objects.filter(is_published=True)
    serializer_class = BlogPostSerializer
    lookup_field = "slug"


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.filter(is_published=True)
    serializer_class = ProjectSerializer
    lookup_field = "slug"


class PublicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publication.objects.filter(is_published=True)
    serializer_class = PublicationSerializer


# Old server-rendered pages. This backend used to serve the site itself, and search
# engines still list some of those URLs. Each one now permanently redirects to its
# page on the real site, so the listing (and its ranking) moves there.


def _site(path):
    return HttpResponsePermanentRedirect(f"{settings.SITE_URL}{path}")


def legacy_page(path):
    return lambda request: _site(path)


def legacy_project(request, stub):
    project = (
        Project.objects.filter(is_published=True, slug=stub).first()
        or Project.objects.filter(is_published=True, title=stub.replace("_", " ")).first()
    )
    return _site(f"/projects/{project.slug}" if project and project.slug else "/projects")


def legacy_post(request, stub):
    # Old post URLs encoded the title: "-" -> "1", " " -> "-", ":" -> "0".
    title = stub.replace("0", ":").replace("-", " ").replace("1", "-")
    post = (
        BlogPost.objects.filter(is_published=True, slug=stub).first()
        or BlogPost.objects.filter(is_published=True, title=title).first()
    )
    return _site(f"/blog/{post.slug}" if post and post.slug else "/blog")
