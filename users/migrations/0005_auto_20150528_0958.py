# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_dareyoouserprofile_ionic_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='user',
            field=models.ForeignKey(related_name='devices', to=settings.AUTH_USER_MODEL),
        ),
    ]
