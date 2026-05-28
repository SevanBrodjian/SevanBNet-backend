from rest_framework import serializers
from .models import BlogPost, Project, Publication


class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'authors_str', 'journal_name', 'status',
            'description', 'url', 'doi', 'site_path',
            'publication_date', 'submission_date',
        ]