# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0013_team_is_fake'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='bwin_name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
