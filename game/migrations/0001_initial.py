# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Fixture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('start_date', models.DateTimeField(null=True, blank=True)),
                ('end_date', models.DateTimeField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='League',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('description', models.CharField(max_length=255, null=True, blank=True)),
                ('pic', models.ImageField(null=True, upload_to=b'leagues', blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.IntegerField(default=0)),
                ('did_share', models.BooleanField(default=False)),
                ('fixture', models.ForeignKey(related_name='matches', blank=True, to='game.Fixture', null=True)),
                ('player', models.ForeignKey(related_name='matches', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True, null=True)),
                ('is_captain', models.BooleanField(default=False)),
                ('state', models.CharField(default=b'state_accepted', max_length=64, null=True, blank=True, choices=[(b'state_waiting_captain', b'Waiting captain'), (b'state_waiting_player', b'Waiting player'), (b'state_accepted', b'Accepted')])),
                ('player', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Pool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, null=True, blank=True)),
                ('slug', models.SlugField(default=b'', max_length=255, null=True, blank=True)),
                ('publishing_date', models.DateTimeField(null=True, blank=True)),
                ('closing_date', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(null=True, blank=True)),
                ('publicated_at', models.DateTimeField(null=True, blank=True)),
                ('closed_at', models.DateTimeField(null=True, blank=True)),
                ('resolved_at', models.DateTimeField(null=True, blank=True)),
                ('state', models.CharField(default=b'state_draft', max_length=64, null=True, blank=True, choices=[(b'state_draft', b'Draft'), (b'state_open', b'Open'), (b'state_closed', b'Closed'), (b'state_set', b'Set')])),
                ('pool_type', models.CharField(default=b'type_quiniela', max_length=64, null=True, blank=True, choices=[(b'type_quiniela', b'Quiniela')])),
                ('public', models.BooleanField(default=True)),
                ('author', models.ForeignKey(related_name='pools_created', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PoolOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('pic', models.ImageField(null=True, upload_to=b'pool_options', blank=True)),
                ('pool', models.ForeignKey(related_name='options', blank=True, to='game.Pool', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PoolResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('players', models.ManyToManyField(related_name='results', to=settings.AUTH_USER_MODEL)),
                ('pool', models.ForeignKey(related_name='results', blank=True, to='game.Pool', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Prize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('description', models.CharField(max_length=255, null=True, blank=True)),
                ('pic', models.ImageField(null=True, upload_to=b'prizes', blank=True)),
                ('order', models.IntegerField(default=1)),
                ('league', models.ForeignKey(related_name='prizes', blank=True, to='game.League', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('pic', models.ImageField(null=True, upload_to=b'teams', blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('players', models.ManyToManyField(related_name='teams', through='game.Membership', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='membership',
            name='team',
            field=models.ForeignKey(to='game.Team'),
        ),
        migrations.AddField(
            model_name='match',
            name='team',
            field=models.ForeignKey(related_name='matches', blank=True, to='game.Team', null=True),
        ),
        migrations.AddField(
            model_name='league',
            name='teams',
            field=models.ManyToManyField(related_name='leagues', to='game.Team'),
        ),
        migrations.AddField(
            model_name='fixture',
            name='league',
            field=models.ForeignKey(related_name='fixtures', blank=True, to='game.League', null=True),
        ),
        migrations.AddField(
            model_name='fixture',
            name='pools',
            field=models.ManyToManyField(related_name='fixtures', to='game.Pool'),
        ),
    ]
