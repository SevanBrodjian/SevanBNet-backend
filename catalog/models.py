from django.db import models
from django.urls import reverse
from django.utils import timezone
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
    ongoing = models.BooleanField()
    topic = models.ManyToManyField(Topic, blank=True, null=True)
    img = models.CharField(max_length=500, blank=True, null=True) #models.ImageField(upload_to='img', max_length=None)
    link = models.CharField(max_length=500, blank=True, null=True)
    association = models.ManyToManyField(Association, blank=True, null=True)

    class Meta:
        ordering = ['-ongoing', '-end', 'title']

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book."""
        uri = self.title.replace(' ', '_')
        return reverse('project-detail', args=[str(uri)])


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    content = models.TextField()
    image = models.CharField(max_length=500, blank=True, null=True)
    published_date = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Generate slug only if it's a new post or the title has changed
        if not self.slug or self.slug != slugify(self.title):
            self.slug = slugify(self.title)
        super(BlogPost, self).save(*args, **kwargs)

    class Meta:
        ordering = ['published_date']

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book."""
        return reverse('blog-post', args=[str(self.slug)])


class Author(models.Model):
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40, blank=True, null=True)
    association = models.ManyToManyField(Association, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        """String for representing the Model object."""
        return self.first_name


class Publication(models.Model):
    title = models.CharField(max_length=200)
    journal_name = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=200)
    description = models.TextField()
    citation = models.TextField(blank=True, null=True)
    doi = models.CharField(max_length=200, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    submission_date = models.DateTimeField(blank=True, null=True)
    publication_date = models.DateTimeField(blank=True, null=True)
    first_author = models.BooleanField()
    authors = models.ManyToManyField(Author, blank=True, null=True)
    association = models.ManyToManyField(Association, blank=True, null=True)
    topic = models.ManyToManyField(Topic, blank=True, null=True)

    class Meta:
        ordering = ['-publication_date', '-submission_date', 'title']

    def __str__(self):
        return self.title