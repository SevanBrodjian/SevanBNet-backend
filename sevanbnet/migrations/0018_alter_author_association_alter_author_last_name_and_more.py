# Generated by Django 4.2.3 on 2023-11-12 02:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sevanbnet', '0017_alter_publication_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='association',
            field=models.ManyToManyField(blank=True, null=True, to='sevanbnet.association'),
        ),
        migrations.AlterField(
            model_name='author',
            name='last_name',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='author',
            name='url',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='image',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='association',
            field=models.ManyToManyField(blank=True, null=True, to='sevanbnet.association'),
        ),
        migrations.AlterField(
            model_name='project',
            name='description',
            field=models.TextField(blank=True, max_length=3000, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='img',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='link',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='topic',
            field=models.ManyToManyField(blank=True, null=True, to='sevanbnet.topic'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='association',
            field=models.ManyToManyField(blank=True, null=True, to='sevanbnet.association'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='authors',
            field=models.ManyToManyField(blank=True, null=True, to='sevanbnet.author'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='citation',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='doi',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='journal_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='publication_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='submission_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='topic',
            field=models.ManyToManyField(blank=True, null=True, to='sevanbnet.topic'),
        ),
        migrations.AlterField(
            model_name='publication',
            name='url',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
