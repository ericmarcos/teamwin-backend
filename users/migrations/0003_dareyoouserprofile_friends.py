# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20150428_1443'),
    ]

    operations = [
        migrations.AddField(
            model_name='dareyoouserprofile',
            name='friends',
            field=models.ManyToManyField(related_name='friends_rel_+', to='users.DareyooUserProfile', blank=True),
        ),
    ]
