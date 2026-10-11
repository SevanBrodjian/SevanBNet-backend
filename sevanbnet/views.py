from django.conf import settings
from django.db.models import Prefetch
from django.http import HttpResponsePermanentRedirect
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import BlogPost, Project, Publication, SiteSettings
from .serializers import (
    PaperSerializer,
    PostSerializer,
    ProjectSerializer,
    SiteSettingsSerializer,
)

# The public API: read-only, and only ever what is marked Visible in the control panel.


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """Every visible project, listed or not; the Projects page shows the listed ones."""

    queryset = Project.objects.filter(visible=True).prefetch_related(
        Prefetch("papers", queryset=Publication.objects.filter(visible=True))
    )
    serializer_class = ProjectSerializer
    lookup_field = "slug"


class PaperViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publication.objects.filter(visible=True).select_related("project")
    serializer_class = PaperSerializer


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlogPost.objects.filter(visible=True)
    serializer_class = PostSerializer
    lookup_field = "slug"


@api_view(["GET"])
def site_settings(request):
    return Response(SiteSettingsSerializer(SiteSettings.load()).data)


# Old server-rendered pages. This backend used to serve the site itself, and search
# engines still list some of those URLs. Each one now permanently redirects to its
# page on the real site, so the listing (and its ranking) moves there.


def _site(path):
    return HttpResponsePermanentRedirect(f"{settings.SITE_URL}{path}")


def legacy_page(path):
    return lambda request: _site(path)


def legacy_project(request, stub):
    project = (
        Project.objects.filter(visible=True, slug=stub).first()
        or Project.objects.filter(visible=True, title=stub.replace("_", " ")).first()
    )
    return _site(f"/projects/{project.slug}" if project else "/projects")


def legacy_post(request, stub):
    # Old post URLs encoded the title: "-" -> "1", " " -> "-", ":" -> "0".
    title = stub.replace("0", ":").replace("-", " ").replace("1", "-")
    post = (
        BlogPost.objects.filter(visible=True, slug=stub).first()
        or BlogPost.objects.filter(visible=True, title=title).first()
    )
    return _site(f"/blog/{post.slug}" if post else "/blog")
