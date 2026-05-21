from django.contrib import admin

from .models import Topic, Association, Project, BlogPost, Publication, QRRedirect, Scan


# Register your models here.
admin.site.register(Topic)
admin.site.register(Association)
admin.site.register(Project)
admin.site.register(BlogPost)
admin.site.register(Publication)


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