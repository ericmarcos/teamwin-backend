# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0003_auto_20150504_1119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fixture',
            name='pools',
            field=models.ManyToManyField(related_name='fixtures', null=True, to='game.Pool', blank=True),
        ),
        migrations.AlterField(
            model_name='league',
            name='teams',
            field=models.ManyToManyField(related_name='leagues', null=True, to='game.Team', blank=True),
        ),
        migrations.AlterField(
            model_name='pool',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='poolresult',
            name='players',
            field=models.ManyToManyField(related_name='results', null=True, to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='players',
            field=models.ManyToManyField(related_name='teams', null=True, through='game.Membership', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
