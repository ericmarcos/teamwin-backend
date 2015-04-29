from django.db import models

from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model


class Pool(models.Model):
    STATE_DRAFT = 'state_draft'
    STATE_OPEN = 'state_open'
    STATE_CLOSED = 'state_closed'
    STATE_SET = 'state_set'
    STATE_CHOICES = (
        (STATE_DRAFT, 'Draft'),
        (STATE_OPEN, 'Open'),
        (STATE_CLOSED, 'Closed'),
        (STATE_SET, 'Set'),
    )

    TYPE_QUINIELA = 'type_quiniela'
    TYPE_CHOICES = (
        (TYPE_QUINIELA, 'Quiniela'),
    )

    title = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, blank=True, null=True, default='')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='pools_created')
    publishing_date = models.DateTimeField(blank=True, null=True)
    closing_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, editable=False)
    publicated_at = models.DateTimeField(blank=True, null=True, editable=False)
    closed_at = models.DateTimeField(blank=True, null=True, editable=False)
    resolved_at = models.DateTimeField(blank=True, null=True, editable=False)
    state = models.CharField(max_length=64, blank=True, null=True, choices=STATE_CHOICES, default=STATE_DRAFT)
    pool_type = models.CharField(max_length=64, blank=True, null=True, choices=TYPE_CHOICES, default=TYPE_QUINIELA)
    public = models.BooleanField(default=True)

    def __unicode__(self):
        return str(self.title)


class PoolOption(models.Model):
    pool = models.ForeignKey(Pool, blank=True, null=True, related_name='options')
    name = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='pool_options', null=True, blank=True)

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url()
        else:
            return ""

    def __unicode__(self):
        return str(self.name)


class PoolResult(models.Model):
    pool = models.ForeignKey(Pool, blank=True, null=True, related_name='results')
    name = models.CharField(max_length=255, blank=True, null=True)
    players = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='results')
    is_winner = models.BooleanField(default=False)

    def __unicode__(self):
        return str(self.name)


class Team(models.Model):
    players = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Membership', related_name='teams')
    name = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='teams', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url()
        else:
            return ""

    def __unicode__(self):
        return str(self.name)


class Membership(models.Model):
    STATE_WAITING_CAPTAIN = 'state_waiting_captain'
    STATE_WAITING_PLAYER = 'state_waiting_player'
    STATE_ACCEPTED = 'state_accepted'
    STATE_CHOICES = (
        (STATE_WAITING_CAPTAIN, "Waiting captain"),
        (STATE_WAITING_PLAYER, "Waiting player"),
        (STATE_ACCEPTED, "Accepted"),
    )

    player = models.ForeignKey(settings.AUTH_USER_MODEL)
    team = models.ForeignKey(Team)
    date_joined = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    is_captain = models.BooleanField(default=False)
    state = models.CharField(max_length=64, blank=True, null=True, choices=STATE_CHOICES, default=STATE_ACCEPTED)


class League(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='leagues', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    teams = models.ManyToManyField(Team, related_name='leagues')

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url()
        else:
            return ""

    def __unicode__(self):
        return str(self.name)


class Prize(models.Model):
    league = models.ForeignKey(League, blank=True, null=True, related_name='prizes')
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='prizes', null=True, blank=True)
    order = models.IntegerField(default=1)

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url()
        else:
            return ""

    def __unicode__(self):
        return str(self.name)


class Fixture(models.Model):
    league = models.ForeignKey(League, blank=True, null=True, related_name='fixtures')
    pools = models.ManyToManyField(Pool, related_name='fixtures')
    name = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return str(self.name)


class Match(models.Model):
    fixture = models.ForeignKey(Fixture, blank=True, null=True, related_name='matches')
    team = models.ForeignKey(Team, blank=True, null=True, related_name='matches')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='matches')
    score = models.IntegerField(default=0)
    did_share = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s - %s - %s: %s" % (str(self.player), str(self.team), str(self.fixture), str(self.score))
