# Generated by Django 4.0.6 on 2022-07-11 14:21

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_alter_project_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='start',
            field=models.DateField(default=datetime.date(2022, 7, 11)),
        ),
    ]
