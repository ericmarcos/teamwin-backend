from operator import itemgetter

from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import get_fb_friends


class PoolQuerySet(models.QuerySet):

    def state(self, state):
        return self.filter(state=state)

    def draft(self):
        return self.state(Pool.STATE_DRAFT)

    def open(self):
        return self.state(Pool.STATE_OPEN)

    def closed(self):
        return self.state(Pool.STATE_CLOSED)

    def set(self):
        return self.state(Pool.STATE_SET)

    def type(self, t):
        return self.filter(pool_type=t)

    def quiniela(self):
        return self.type(Pool.TYPE_QUINIELA)

    def public(self):
        return self.filter(public=True)

    def played(self, player):
        return self.filter(results__players=player).distinct()

    def pending(self, player):
        return self.open().filter(fixtures__league__teams__players=player).exclude(results__players=player).distinct()


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

    objects = PoolQuerySet.as_manager()

    title = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, blank=True, null=True, default='')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='pools_created')
    publishing_date = models.DateTimeField(blank=True, null=True)
    closing_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    publicated_at = models.DateTimeField(blank=True, null=True, editable=False)
    closed_at = models.DateTimeField(blank=True, null=True, editable=False)
    resolved_at = models.DateTimeField(blank=True, null=True, editable=False)
    state = models.CharField(max_length=64, blank=True, null=True, choices=STATE_CHOICES, default=STATE_DRAFT)
    pool_type = models.CharField(max_length=64, blank=True, null=True, choices=TYPE_CHOICES, default=TYPE_QUINIELA)
    public = models.BooleanField(default=True)

    def play(self, player, result):
        r = PoolResult.objects.get_or_create(pool=self, name=result)
        r.players.add(player)
        for team in player.teams.all():
            for fixture in self.fixtures.all():
                m, created = Match.objects.get_or_create(team=team, fixture=fixture, player=player)
                m.played += 1
                m.save()

    def set(self, result):
        r = PoolResult.objects.get_or_create(pool=self, name=result)
        r.is_winner = True
        r.save()
        Match.objects.filter(fixture__pools=self).update(score=models.F('score') + 1)

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
    players = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='results')
    is_winner = models.BooleanField(default=False)

    def __unicode__(self):
        return str(self.name)


class PlayerBelongsToTooManyTeams(Exception):
    def __init__(self, user, *args, **kwargs):
        super(Exception, self).__init__('The user %s belongs to too many teams' % user.id)


class TeamHasToTooManyPlayers(Exception):
    def __init__(self, team, *args, **kwargs):
        super(Exception, self).__init__('The team %s has too many players' % team.id)


class CaptainCantLeave(Exception):
    def __init__(self, *args, **kwargs):
        super(Exception, self).__init__('The captain can\'t leave the team')


class TeamQuerySet(models.QuerySet):

    def friends(self, user):
        fr = get_fb_friends(user)
        return self.filter(players=fr).exclude(players=user).distinct()


class Team(models.Model):
    objects = TeamQuerySet.as_manager()

    players = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, through='Membership', related_name='teams')
    name = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='teams', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)

    def captain(self):
        return self.players.filter(membership__is_captain=True).first()

    def is_captain(self, user):
        return self.players.filter(membership__is_captain=True, id=user.id).exists()

    def active_players(self):
        return self.players.filter(membership__state=Membership.STATE_ACTIVE)

    def waiting_captain(self):
        return self.players.filter(membership__state=Membership.STATE_WAITING_CAPTAIN)

    def waiting_players(self):
        return self.players.filter(membership__state=Membership.STATE_WAITING_PLAYER)

    def check_user(self, user):
        active_teams = Membership.objects.filter(player=user, state=Membership.STATE_ACTIVE).count()
        if not user.profile.is_pro and active_teams >= settings.DAREYOO_MAX_TEAMS:
            raise PlayerBelongsToTooManyTeams(user)
        active_players = Membership.objects.filter(team=self, state=Membership.STATE_ACTIVE).count()
        if active_players >= settings.DAREYOO_MAX_PLAYERS:
            raise TeamHasToTooManyPlayers(self)

    def request_enroll(self, user):
        self.check_user(user)
        m, created = Membership.objects.get_or_create(team=self, player=user)
        if created:
            m.state = m.STATE_WAITING_CAPTAIN
            # TODO send request to captain
        elif m.state == m.STATE_WAITING_PLAYER:
            m.state = m.STATE_ACTIVE
        else:
            return False
        m.save()
        return m.state

    def sign(self, user):
        m, created = Membership.objects.get_or_create(team=self, player=user)
        if created:
            m.state = m.STATE_WAITING_PLAYER
            #send request to player
        elif m.state == m.STATE_WAITING_CAPTAIN:
            self.check_user()
            m.state = m.STATE_ACTIVE
        else:
            return False
        m.save()
        return m.state

    def fire(self, user):
        m = Membership.objects.get(team=self, player=user)
        if m.is_captain:
            raise CaptainCantLeave
        m.delete()
        for f in self.current_fixtures():
            Match.objects.filter(player=user, team=self, fixture=f).delete()
        return m.state

    def current_fixtures(self):
        return [league.current_fixture() for league in self.leagues.all()]

    def prev_fixtures(self):
        return [league.prev_fixture() for league in self.leagues.all()]

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
    STATE_ACTIVE = 'state_active'
    STATE_CHOICES = (
        (STATE_WAITING_CAPTAIN, "Waiting captain"),
        (STATE_WAITING_PLAYER, "Waiting player"),
        (STATE_ACTIVE, "Active"),
    )

    player = models.ForeignKey(settings.AUTH_USER_MODEL)
    team = models.ForeignKey(Team)
    date_joined = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    is_captain = models.BooleanField(default=False)
    state = models.CharField(max_length=64, blank=True, null=True, choices=STATE_CHOICES, default=STATE_ACTIVE)


class League(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='leagues', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    teams = models.ManyToManyField(Team, blank=True, related_name='leagues')
    visible = models.BooleanField(default=True)

    def current_fixture(self):
        now = timezone.now()
        return self.fixtures.current().first()

    def prev_fixture(self, prev=1):
        now = timezone.now()
        return self.fixtures.prev(prev).first()

    def team_leaderboard(self, team, prev=0):
        leaderboard = []
        fixture = self.fixtures.prev(prev).first()
        if not fixture:
            return leaderboard
        for p in team.active_players():
            m, created = Match.objects.get_or_create(team=team, fixture=fixture, player=p)
            leaderboard.append({'player_id': p.id, 'played': m.played, 'score': m.score})
        leaderboard.sort(key=itemgetter('score'), reverse=True)
        return leaderboard

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


class FixtureQuerySet(models.QuerySet):

    def current(self):
        now = timezone.now()
        return self.filter(start_date__lte=now, end_date__gte=now)

    def prev(self, prev=0):
        now = timezone.now()
        return self.filter(start_date__lte=now).order_by('-end_date')[prev:]


class Fixture(models.Model):
    objects = FixtureQuerySet.as_manager()

    league = models.ForeignKey(League, blank=True, null=True, related_name='fixtures')
    pools = models.ManyToManyField(Pool, blank=True, related_name='fixtures')
    name = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return str(self.name)


class Match(models.Model):
    fixture = models.ForeignKey(Fixture, blank=True, null=True, related_name='matches')
    team = models.ForeignKey(Team, blank=True, null=True, related_name='matches')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='matches')
    played = models.IntegerField(default=0) #Number of pools played
    score = models.IntegerField(default=0)
    did_share = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s - %s - %s: %s" % (str(self.player), str(self.team), str(self.fixture), str(self.score))
