# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_dareyoouserprofile_friends'),
    ]

    operations = [
        migrations.AddField(
            model_name='dareyoouserprofile',
            name='ionic_id',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
