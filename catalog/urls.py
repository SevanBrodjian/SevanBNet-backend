from django.urls import path, re_path
from django.conf.urls.static import static
from . import views
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('', views.home, name='home'),
    path('projects/', views.ProjectListView.as_view(), name='projects'),
    path('resume/', views.resume, name='resume'),
    path('contact/', views.contact, name='contact'),
    re_path(r'^projects/(?P<stub>[-\w]+)$', views.project_detail_view, name='project-detail'),
]