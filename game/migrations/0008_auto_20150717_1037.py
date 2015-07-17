# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0007_auto_20150630_1045'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fixture',
            name='pools',
        ),
        migrations.AddField(
            model_name='pool',
            name='fixtures',
            field=models.ManyToManyField(related_name='pools', to='game.Fixture', blank=True),
        ),
    ]
