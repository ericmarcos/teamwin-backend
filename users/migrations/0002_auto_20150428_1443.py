# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dareyoouserprofile',
            name='gender',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dareyoouserprofile',
            name='locale',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dareyoouserprofile',
            name='location',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='dareyoouserprofile',
            name='timezone',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='dareyoouserprofile',
            name='user',
            field=models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
