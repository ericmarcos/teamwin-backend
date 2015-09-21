# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0014_item_bwin_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='poolresult',
            name='bwin_odds',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
