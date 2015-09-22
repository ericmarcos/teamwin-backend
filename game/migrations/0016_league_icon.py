# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0015_poolresult_bwin_odds'),
    ]

    operations = [
        migrations.AddField(
            model_name='league',
            name='icon',
            field=models.ImageField(null=True, upload_to=b'leagues_icons', blank=True),
        ),
    ]
