from django.contrib import admin

from .models import Topic, Association, Project, BlogPost, Publication, QRRedirect, Scan


admin.site.register(Topic)
admin.site.register(Association)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'start', 'end')
    list_filter = ('is_published',)
    list_editable = ('is_published',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'published_date')
    list_filter = ('is_published',)
    list_editable = ('is_published',)


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'status', 'publication_date')
    list_filter = ('is_published',)
    list_editable = ('is_published',)


@admin.register(QRRedirect)
class QRRedirectAdmin(admin.ModelAdmin):
    list_display  = ('label', 'short_code', 'target_url', 'is_active', 'created_at')
    list_filter   = ('is_active',)
    search_fields = ('label', 'short_code', 'target_url')
    readonly_fields = ('created_at',)


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display  = ('redirect', 'timestamp', 'ip_address', 'user_agent')
    list_filter   = ('redirect',)
    readonly_fields = ('redirect', 'timestamp', 'ip_address', 'user_agent', 'referrer')