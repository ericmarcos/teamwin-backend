# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_auto_20150505_0852'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fixture',
            name='pools',
            field=models.ManyToManyField(related_name='fixtures', to='game.Pool', blank=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='teams',
            field=models.ManyToManyField(related_name='leagues', to='game.Team', blank=True),
        ),
        migrations.AlterField(
            model_name='poolresult',
            name='players',
            field=models.ManyToManyField(related_name='results', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='players',
            field=models.ManyToManyField(related_name='teams', through='game.Membership', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
