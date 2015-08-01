# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0010_auto_20150729_1529'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pool',
            options={'ordering': ['-closing_date']},
        ),
        migrations.AddField(
            model_name='match',
            name='extra_data',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='match',
            name='extra_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='match',
            name='extra_type',
            field=models.CharField(blank=True, max_length=255, null=True, choices=[(b'extra_type_share_fb', b'Share Facebook'), (b'extra_type_rate', b'Rate'), (b'extra_type_feedback', b'Feedback'), (b'extra_type_ad', b'Watch Ad'), (b'extra_type_visit', b'Visit Website'), (b'extra_type_download', b'Download')]),
        ),
    ]
