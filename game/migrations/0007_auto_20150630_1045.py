# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_league_visible'),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('short_name', models.CharField(max_length=255, null=True, blank=True)),
                ('number', models.CharField(max_length=255, null=True, blank=True)),
                ('pic', models.ImageField(null=True, upload_to=b'items', blank=True)),
                ('color', models.CharField(max_length=255, null=True, blank=True)),
                ('second_color', models.CharField(max_length=255, null=True, blank=True)),
                ('parent', models.ForeignKey(related_name='members', blank=True, to='game.Item', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='pooloption',
            name='item',
            field=models.ForeignKey(related_name='pool_options', blank=True, to='game.Item', null=True),
        ),
    ]
