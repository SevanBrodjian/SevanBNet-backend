from django.db import models
from django.urls import reverse
from django.utils import timezone


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
    description = models.TextField(blank=True, max_length=3000)
    start = models.DateField(default=timezone.now)
    end = models.DateField(blank=True, null=True)
    ongoing = models.BooleanField()
    topic = models.ManyToManyField(Topic, blank=True)
    img = models.ImageField(upload_to='img', max_length=None)
    link = models.CharField(max_length=500, blank=True)
    association = models.ManyToManyField(Association, blank=True)

    class Meta:
        ordering = ['-ongoing', '-end', 'title']

    def __str__(self):
        """String for representing the Model object."""
        return self.title

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book."""
        uri = self.title.replace(' ', '_')
        return reverse('project-detail', args=[str(uri)])