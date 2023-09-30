from django.contrib import admin

from .models import Topic, Association, Project, BlogPost

# Register your models here.
admin.site.register(Topic)
admin.site.register(Association)
admin.site.register(Project)
admin.site.register(BlogPost)