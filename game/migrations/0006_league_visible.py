# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_auto_20150505_0853'),
    ]

    operations = [
        migrations.AddField(
            model_name='league',
            name='visible',
            field=models.BooleanField(default=True),
        ),
    ]
