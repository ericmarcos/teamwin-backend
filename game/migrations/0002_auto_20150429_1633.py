# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='poolresult',
            name='is_winner',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='pool',
            name='closed_at',
            field=models.DateTimeField(null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='pool',
            name='created_at',
            field=models.DateTimeField(null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='pool',
            name='publicated_at',
            field=models.DateTimeField(null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='pool',
            name='resolved_at',
            field=models.DateTimeField(null=True, editable=False, blank=True),
        ),
    ]
