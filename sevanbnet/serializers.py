from rest_framework import serializers

from .models import BlogPost, Project, Publication, SiteSettings, youtube_id


class BlanksAsNull(serializers.ModelSerializer):
    """Optional text left blank in the admin is sent as null, never as ""."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {k: (None if v == "" else v) for k, v in data.items()}


class ProjectSerializer(BlanksAsNull):
    media = serializers.SerializerMethodField()
    description_html = serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = [
            "slug",
            "title",
            "listed",
            "rank",
            "start",
            "end",
            "summary",
            "thumbnail",
            "glow",
            "media",
            "source",
            "description",
            "description_html",
        ]

    def get_media(self, p):
        if not (p.media_kind and p.media):
            return None
        if p.media_kind == Project.YOUTUBE:
            return {"kind": "youtube", "id": youtube_id(p.media)}
        if p.media_kind == Project.CODE:
            return {"kind": "code", "text": p.media}
        media = {"kind": p.media_kind, "src": p.media}
        if p.media_kind == Project.VIDEO:
            media["poster"] = p.media_poster or None
        else:
            media["alt"] = p.media_alt
        return media | {"width": p.media_width, "height": p.media_height}


class PaperSerializer(BlanksAsNull):
    project = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = [
            "id",
            "key",
            "title",
            "authors",
            "venue",
            "status",
            "date",
            "paper_url",
            "project",
            "project_url",
            "bibtex",
            "description",
            "rank",
        ]

    def get_project(self, paper):
        # A hidden project has no page, so the paper simply stops linking to it.
        p = paper.project
        if p is None or not p.visible:
            return None
        return {"slug": p.slug, "title": p.title, "source": p.source or None}


class PostSerializer(BlanksAsNull):
    class Meta:
        model = BlogPost
        fields = ["slug", "title", "description", "date"]


class SiteSettingsSerializer(serializers.ModelSerializer):
    # The plain paragraphs stay for search engines and llms.txt; the page shows the HTML.
    about = serializers.ListField(source="about_paragraphs", child=serializers.CharField())
    about_html = serializers.ReadOnlyField()
    writing_note_html = serializers.ReadOnlyField()

    class Meta:
        model = SiteSettings
        fields = ["home_line", "role", "about", "about_html", "writing_note", "writing_note_html"]
