# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_auto_20150429_1633'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='played',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='membership',
            name='state',
            field=models.CharField(default=b'state_active', max_length=64, null=True, blank=True, choices=[(b'state_waiting_captain', b'Waiting captain'), (b'state_waiting_player', b'Waiting player'), (b'state_active', b'Active')]),
        ),
    ]
