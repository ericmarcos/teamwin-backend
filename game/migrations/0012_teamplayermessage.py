# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('game', '0011_auto_20150801_1844'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamPlayerMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.CharField(max_length=255, null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('player', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('team', models.ForeignKey(blank=True, to='game.Team', null=True)),
            ],
        ),
    ]
