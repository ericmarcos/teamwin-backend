# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_auto_20150727_1049'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pooloption',
            options={'ordering': ['id']},
        ),
        migrations.RenameField(
            model_name='match',
            old_name='did_share',
            new_name='extra_points',
        ),
    ]
