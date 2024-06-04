from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.db.models import Case, When, Value
from django.utils.text import slugify


class Topic(models.Model):
    """Model representing a project topic."""
    name = models.CharField(max_length=40)

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Association(models.Model):
    """Model representing a project topic."""
    name = models.CharField(max_length=40)

    def __str__(self):
        """String for representing the Model object."""
        return self.name


class Project(models.Model):
    """Model representing a project"""
    title = models.CharField(max_length=100)
    independent = models.BooleanField()
    description = models.TextField(blank=True, null=True)
    start = models.DateField(default=timezone.now)
    end = models.DateField(blank=True, null=True)
    topic = models.ManyToManyField(Topic, blank=True)
    img = models.CharField(max_length=500, blank=True, null=True) 
    link = models.CharField(max_length=500, blank=True, null=True)
    association = models.ManyToManyField(Association, blank=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        ordering = [
            Case(
                When(end__isnull=True, then=Value(0)),
                default=Value(1),
                output_field=models.IntegerField(),
            ),
            '-end',
            'title'
        ]

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this project."""
        return reverse('project-detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()
    published_date = models.DateField(default=timezone.now)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        ordering = ['published_date']

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book."""
        stub = self.title.replace('-', '1').replace(' ', '-').replace(':', '0')
        return reverse('blog-post', args=[str(stub)])


class Publication(models.Model):
    title = models.CharField(max_length=200)
    journal_name = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=1000)
    description = models.TextField()
    citation = models.TextField(blank=True, null=True)
    doi = models.CharField(max_length=200, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    submission_date = models.DateTimeField(blank=True, null=True)
    publication_date = models.DateTimeField(blank=True, null=True)
    first_author = models.BooleanField()
    authors_str = models.CharField(max_length=400, blank=True, null=True)
    association = models.ManyToManyField(Association, blank=True)
    topic = models.ManyToManyField(Topic, blank=True)
    rank = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['rank', '-publication_date', '-submission_date', 'title']

    def __str__(self):
        return self.title