# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0005_auto_20150528_0958'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserActivation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('level', models.IntegerField(default=1, null=True, blank=True)),
                ('user', models.ForeignKey(related_name='activations', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
