# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0012_teamplayermessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='is_fake',
            field=models.BooleanField(default=False),
        ),
    ]
