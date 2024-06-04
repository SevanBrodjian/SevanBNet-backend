from django.contrib import admin
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path, include
from django.conf.urls.static import static
from django.views.static import serve
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'blogposts', views.BlogPostViewSet)
router.register(r'projects', views.ProjectViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='home/', permanent=True)),
    
    path('home/', views.home, name='home'),
    path('projects/', views.ProjectListView.as_view(), name='projects'),
    path('blog/', views.blog, name='blog'),
    path('research/', views.research, name='research'),

    re_path(r'^projects/(?P<stub>[-\w]+)$', views.project_detail_view, name='project-detail'),
    re_path(r'^blog/(?P<stub>[A-Za-z0-9-]+)$', views.blog_post, name='blog-post'),

    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^staticfiles/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),

    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)