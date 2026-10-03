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
