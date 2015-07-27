# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_auto_20150717_1037'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prize',
            name='description',
            field=models.TextField(null=True, blank=True),
        ),
    ]
