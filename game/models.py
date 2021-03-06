#!/usr/bin/env python
# -*- coding: utf-8 -*-

from operator import itemgetter

from celery import shared_task
from django.conf import settings
from django.db import models
from django.db.models import Sum, Count, Q, F, When, Case, Value, Prefetch
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import *


class PlayerBelongsToTooManyTeams(Exception):
    def __init__(self, user, *args, **kwargs):
        super(Exception, self).__init__('The user %s belongs to too many teams' % user.id)


class TeamHasToTooManyPlayers(Exception):
    def __init__(self, team, *args, **kwargs):
        super(Exception, self).__init__('The team %s has too many players' % team.id)


class CaptainCantLeave(Exception):
    def __init__(self, *args, **kwargs):
        super(Exception, self).__init__('The captain can\'t leave the team')


class NotCaptain(Exception):
    def __init__(self, *args, **kwargs):
        super(Exception, self).__init__('Only the captain of the team can do this')


class TooManyLeagues(Exception):
    def __init__(self, team, *args, **kwargs):
        super(Exception, self).__init__('The team %s is enrolled in too many leagues' % team.id)


class InvalidPoolTransition(Exception):
    def __init__(self, state1, state2, *args, **kwargs):
        super(Exception, self).__init__('Invalid pool transition from state %s to state %s' % (state1, state2))


class CantPlayPool(Exception):
    def __init__(self, pool, *args, **kwargs):
        super(Exception, self).__init__('Can\'t play pool %s (state %s)' % (pool.id, pool.state))


class InvalidPoolResult(Exception):
    def __init__(self, result, *args, **kwargs):
        super(Exception, self).__init__('Invalid pool result %s' % result)


def check_user_limits(user):
    active_teams = Membership.objects.filter(player=user, state=Membership.STATE_ACTIVE).count()
    if not user.profile.is_pro and active_teams >= settings.DAREYOO_MAX_TEAMS:
        raise PlayerBelongsToTooManyTeams(user)

### This function will be stuffed into the default user model in apps.py
def get_user_points(user):
    if hasattr(user, 'match') and len(user.match) > 0:
        return user.match[0].score
    return 0

def get_user_played(user):
    if hasattr(user, 'match') and len(user.match) > 0:
        return user.match[0].played
    return 0

def get_user_extra_points(user):
    if hasattr(user, 'match') and len(user.match) > 0:
        return user.match[0].extra_points
    return 0


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
        f = Fixture.objects.current().filter(league__teams__players=player)
        return self.open().filter(fixtures=f).exclude(results__players=player).distinct()

    def current(self, player):
        #Temporal solution for users that didn't update to new version of the app
        f = Fixture.objects.current().filter(league__id=1)
        return self.filter(fixtures=f).distinct()

    def current2(self, player):
        f = Fixture.objects.current().filter(league__teams__players=player)
        return self.filter(fixtures=f).distinct()


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
    fixtures = models.ManyToManyField('Fixture', blank=True, related_name='pools')

    def save(self, *args, **kwargs):
        prev_pool = None
        if self.pk:
            prev_pool = Pool.objects.get(pk=self.pk)
        super(Pool, self).save(*args, **kwargs)
        if self.pk and self.publishing_date and (not prev_pool or self.publishing_date != prev_pool.publishing_date):
            self.publish_pool.apply_async([self.id], eta=self.publishing_date)
        if self.pk and self.closing_date and (not prev_pool or self.closing_date != prev_pool.closing_date):
            self.close_pool.apply_async([self.id], eta=self.closing_date)

    @staticmethod
    @shared_task
    def publish_pool(pool_id):
        try:
            p = Pool.objects.get(id=pool_id)
            p.publish()
        except Exception as e:
            print e

    def publish(self):
        if self.state == self.STATE_DRAFT:
            self.state = self.STATE_OPEN
            self.publicated_at = timezone.now()
            self.save()
        else:
            raise InvalidPoolTransition(self.state, self.STATE_OPEN)

    def is_draft(self):
        return self.state == self.STATE_DRAFT

    def is_open(self):
        return self.state == self.STATE_OPEN

    def is_closed(self):
        return self.state == self.STATE_CLOSED

    def is_set(self):
        return self.state == self.STATE_SET

    def play(self, player, result):
        if self.state == self.STATE_OPEN:
            if not result:
                raise InvalidPoolResult(result)
            if self.closing_date and self.closing_date < timezone.now():
                self.close()
                raise CantPlayPool(self)
            if PoolResult.objects.filter(players=player, pool=self).exists() and not player.is_staff and not player.profile.is_pro:
                raise CantPlayPool(self)
            r, created = PoolResult.objects.get_or_create(pool=self, name=result)
            r.players.add(player)
            for team in player.teams.filter(membership__state=Membership.STATE_ACTIVE):
                for fixture in self.fixtures.all():
                    m, created = Match.objects.get_or_create(team=team, fixture=fixture, player=player)
                    m.played += 1
                    m.save()
        else:
            raise CantPlayPool(self)

    @staticmethod
    @shared_task
    def close_pool(pool_id):
        try:
            p = Pool.objects.get(id=pool_id)
            p.close()
        except Exception as e:
            print e

    def close(self):
        if self.state == self.STATE_OPEN:
            self.state = self.STATE_CLOSED
            self.closed_at = timezone.now()
            self.save()
        else:
            raise InvalidPoolTransition(self.state, self.STATE_CLOSED)

    def set(self, result):
        if self.state == self.STATE_OPEN or self.state == self.STATE_CLOSED:
            if not result:
                raise InvalidPoolResult(result)
            r, created = PoolResult.objects.get_or_create(pool=self, name=result)
            r.is_winner = True
            r.save()
            if self.state == self.STATE_OPEN:
                self.closed_at = timezone.now()
            self.state = self.STATE_SET
            self.resolved_at = timezone.now()
            self.save()
            Match.objects.filter(fixture__pools=self, player__results=r).update(score=F('score') + 1)
            for f in self.fixtures.all():
                f.check_winner.delay(f.id)
        else:
            raise InvalidPoolTransition(self.state, self.STATE_SET)

    def players(self):
        return get_user_model().objects.filter(results__pool=self)

    def winners(self):
        pr = self.winner_result()
        if pr:
            return pr.players.all()
        return []

    def winner_result(self):
        return self.results.filter(is_winner=True).first()

    def __unicode__(self):
        if self.title:
            return unicode(self.title)
        options = list(self.options.all())
        if len(options) > 0:
            return " - ".join(map(unicode, options))
        return "Pool %s" % self.id

    class Meta:
        app_label = 'game'
        ordering = ['-closing_date',]


class Item(models.Model):
    parent = models.ForeignKey("self", blank=True, null=True, related_name="members")
    name = models.CharField(max_length=255, blank=True, null=True)
    bwin_name = models.CharField(max_length=255, blank=True, null=True)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    number = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='items', null=True, blank=True)
    color = models.CharField(max_length=255, blank=True, null=True)
    second_color = models.CharField(max_length=255, blank=True, null=True)

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url().split('?')[0]
        else:
            return ""

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        app_label = 'game'
        ordering = ['name',]


class PoolOption(models.Model):
    pool = models.ForeignKey(Pool, blank=True, null=True, related_name='options')
    item = models.ForeignKey(Item, blank=True, null=True, related_name='pool_options')
    name = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='pool_options', null=True, blank=True)

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url().split('?')[0]
        else:
            return ""

    def __unicode__(self):
        if self.name:
            return unicode(self.name)
        try:
            return unicode(self.item)
        except:
            return "PoolOption %s" % self.id

    class Meta:
        app_label = 'game'
        ordering = ['id',]


class PoolResult(models.Model):
    pool = models.ForeignKey(Pool, blank=True, null=True, related_name='results')
    name = models.CharField(max_length=255, blank=True, null=True)
    players = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='results')
    is_winner = models.BooleanField(default=False)
    bwin_odds = models.FloatField(blank=True, null=True)

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        app_label = 'game'


class TeamQuerySet(models.QuerySet):

    def friends(self, user):
        fr = user.profile.friends.all()
        return self.filter(players__profile=fr).exclude(players=user).distinct()

    def active(self):
        return self.filter(membership__state=Membership.STATE_ACTIVE)

    def pending(self):
        return self.filter(Q(membership__state=Membership.STATE_WAITING_CAPTAIN)\
         | Q(membership__state=Membership.STATE_WAITING_PLAYER))


def get_default_team_pic(team_id):
    return settings.DEFAULT_TEAM_PIC_URL % ((team_id or 1) % 10)


class Team(models.Model):
    objects = TeamQuerySet.as_manager()

    players = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, through='Membership', related_name='teams')
    name = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='teams', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    is_fake = models.BooleanField(default=False)

    def set_captain(self, user, check=True):
        if check:
            self.check_limits(user)
        Membership.objects.create(team=self, player=user, is_captain=True)

    def captain(self):
        return self.players.filter(membership__is_captain=True).first()

    def is_captain(self, user):
        return self.players.filter(membership__is_captain=True, id=user.id).exists()

    def is_waiting_captain(self, user):
        return self.players.filter(membership__state=Membership.STATE_WAITING_CAPTAIN, id=user.id).exists()

    def is_waiting_player(self, user):
        return self.players.filter(membership__state=Membership.STATE_WAITING_PLAYER, id=user.id).exists()

    def get_state(self, user):
        m = Membership.objects.filter(player=user, team=self).first()
        if m:
            return m.state
        return None

    def active_players(self):
        return self.players.filter(membership__state=Membership.STATE_ACTIVE)

    def waiting_captain(self):
        return self.players.filter(membership__state=Membership.STATE_WAITING_CAPTAIN)

    def waiting_players(self):
        return self.players.filter(membership__state=Membership.STATE_WAITING_PLAYER)

    def check_limits(self, user):
        check_user_limits(user)
        if self.active_players().count() >= settings.DAREYOO_MAX_PLAYERS:
            raise TeamHasToTooManyPlayers(self)

    @property
    def points(self):
        if hasattr(self, 'sum_points'):
            return self.sum_points
        return 0

    def request_enroll(self, user):
        self.check_limits(user)
        m, created = Membership.objects.get_or_create(team=self, player=user)
        if created:
            if Membership.objects.filter(player=user).count() == 1:
                user.profile.invited_by = self.captain()
                user.profile.save()
                payload = { "$state": "tab.team-detail.current", "$stateParams": "{\"teamId\": %s}" % self.id, "teamId": self.id }
                send_push.delay([self.captain().id], u"%s se ha unido a tu equipo %s" % (user.username, self.name), payload)
            else:
                m.state = m.STATE_WAITING_CAPTAIN
                payload = { "$state": "tab.team-detail.current", "$stateParams": "{\"teamId\": %s}" % self.id, "teamId": self.id }
                send_push.delay([self.captain().id], u"%s ha pedido unirse a tu equipo %s" % (user.username, self.name), payload)
        elif m.state == m.STATE_WAITING_PLAYER:
            m.state = m.STATE_ACTIVE
            payload = { "$state": "tab.team-detail.current", "$stateParams": "{\"teamId\": %s}" % self.id, "teamId": self.id }
            send_push.delay([self.captain().id], u"%s se ha unido a tu equipo %s" % (user.username, self.name), payload)
            for f in self.current_fixtures():
                p = Pool.objects.filter(fixtures=f, results__players=user).count()
                #If you join a team in the middle of a fixture, I won't count the winning pools
                #I want to avoid people creating teams of winning players on the fly...
                #w = Pool.objects.filter(fixture=f, results=PoolResult.objects.filter(players=user, is_winner=True)).count()
                Match.objects.create(player=user, team=self, fixture=f, played=p)
        else:
            return False
        m.save()
        return m.state

    def sign(self, user):
        m, created = Membership.objects.get_or_create(team=self, player=user)
        if created:
            m.state = m.STATE_WAITING_PLAYER
            payload = { "$state": "tab.teams.waiting" }
            send_push.delay([user.id], u"¡%s, capitán del equipo %s, quiere ficharte!" % (self.captain().username, self.name), payload)
        elif m.state == m.STATE_WAITING_CAPTAIN:
            self.check_limits(user)
            m.state = m.STATE_ACTIVE
            payload = { "$state": "tab.team-detail.current", "$stateParams": "{\"teamId\": %s}" % self.id, "teamId": self.id }
            send_push.delay([user.id], u"¡Felicidades! %s, capitán del equipo %s, ha aceptado tu fichaje." % (self.captain().username, self.name), payload)
            for f in self.current_fixtures():
                p = Pool.objects.filter(fixtures=f, results__players=user).count()
                w = Pool.objects.filter(fixtures=f, results=PoolResult.objects.filter(players=user, is_winner=True)).count()
                Match.objects.create(player=user, team=self, fixture=f, played=p)
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

    def call_players(self, user, message):
        recipients = [u.id for u in self.active_players() if u != user]
        send_push.delay(recipients, u"%s de %s: %s" % (user.first_name, self.name, message))
        TeamPlayerMessage.objects.create(player=user, team=self, message=message)

    def current_fixtures(self):
        return [league.current_fixture() for league in self.leagues.all()]

    def prev_fixtures(self):
        return [league.prev_fixture() for league in self.leagues.all()]

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url().split('?')[0]
        else:
            return get_default_team_pic(self.id)

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        ordering = ['name',]
        app_label = 'game'


class TeamPlayerMessage(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    team = models.ForeignKey(Team, blank=True, null=True)
    message = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)

    def __unicode__(self):
        return '%s - %s: %s' % (self.player, self.team, self.message)

    class Meta:
        app_label = 'game'


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

    class Meta:
        app_label = 'game'


class LeagueQuerySet(models.QuerySet):

    def visible(self):
        return self.filter(visible=True)


class League(models.Model):
    objects = LeagueQuerySet.as_manager()

    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='leagues', null=True, blank=True)
    icon = models.ImageField(upload_to='leagues_icons', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    teams = models.ManyToManyField(Team, blank=True, related_name='leagues')
    visible = models.BooleanField(default=True)

    def current_fixture(self):
        return self.fixtures.current().first()

    def prev_fixture(self, prev=1):
        return self.fixtures.prev(prev).first()

    def team_leaderboard(self, team, prev=0, fixture=None):
        fixture = fixture or self.fixtures.prev(prev).first()
        if not fixture:
            return []
        subq = Match.objects.filter(fixture=fixture, team=team)
        if prev:
            lb = get_user_model().objects.filter(matches=subq)
        else:
            lb = team.players.filter(membership__state=Membership.STATE_ACTIVE)
        lb = lb.prefetch_related('profile', Prefetch('matches', queryset=subq, to_attr='match'))
        return sorted(lb, key=lambda x: x.points, reverse=True)

    def leaderboard(self, prev=0, user=None, fixture=None):
        '''
        If user is passed, the returned result will merge the teams of that user to the leaderboard
        with the score of the corresponding fixture
        '''
        fixture = fixture or self.fixtures.prev(prev).first()
        if not fixture:
            return []
        all_teams = Team.objects.filter(matches__fixture=fixture)
        if not prev:
            all_teams = self.teams.all()
        user_teams = all_teams.filter(membership=Membership.objects.filter(player=user, state=Membership.STATE_ACTIVE)) if user else Team.objects.none()
        all_teams = all_teams.annotate(sum_points=Sum(Case(When(matches__fixture=fixture, then='matches__score'))))
        user_teams_points = user_teams.annotate(sum_points=Sum(Case(When(matches__fixture=fixture, then='matches__score'))))
        lb = list(all_teams.order_by('-sum_points')[:10])
        #adding user teams that are not in the top 10
        lb.extend([team for team in user_teams_points if team not in lb])
        #adding user teams that have no matches created yet (the last annotation removes them)
        lb.extend([team for team in user_teams if team not in lb])
        return sorted(lb, key=lambda x: x.sum_points, reverse=True)

    def enroll(self, user, team_id):
        t = Team.objects.get(id=team_id)
        if not t.is_captain(user):
            raise NotCaptain
        if t.leagues.count() >= settings.DAREYOO_MAX_LEAGUES:
            raise TooManyLeagues(t)
        self.teams.add(t)
        f = self.current_fixture()
        if f and not Match.objects.filter(fixture=f, team=t).exists():
            matches = []
            for p in t.active_players():
                matches.append(Match(fixture=f, team=t, player=p))
            Match.objects.bulk_create(matches)

    def leave(self, user, team_id):
        t = Team.objects.get(id=team_id)
        if not t.is_captain(user):
            raise NotCaptain
        self.teams.remove(t)
        f = self.current_fixture()
        if f:
            Match.objects.filter(fixture=f, team=t).delete()

    def extra_points(self, player, etype, data=None):
        Match.objects.filter(fixture=self.current_fixture(), player=player, extra_points=False).update(
            score=F('score') + 2,
            extra_points=True,
            extra_type=etype,
            extra_data=data,
            extra_date=timezone.now()
        )

    def pools(self, prev=0):
        return Pool.objects.filter(fixtures=self.fixtures.prev(prev).first())

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url().split('?')[0]
        else:
            return ""

    def get_icon_url(self):
        if self.icon:
            return self.icon._get_url().split('?')[0]
        else:
            return ""

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        app_label = 'game'


class Prize(models.Model):
    league = models.ForeignKey(League, blank=True, null=True, related_name='prizes')
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    pic = models.ImageField(upload_to='prizes', null=True, blank=True)
    order = models.IntegerField(default=1)

    def get_pic_url(self):
        if self.pic:
            return self.pic._get_url().split('?')[0]
        else:
            return ""

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        app_label = 'game'


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
    name = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super(Fixture, self).save(*args, **kwargs)
        self.start_fixture.apply_async([self.id], eta=self.start_date)

    @staticmethod
    @shared_task
    def start_fixture(fixture_id):
        now = timezone.now()
        f = Fixture.objects.get(id=fixture_id)
        if now > f.start_date and now < f.end_date and f.matches.count() == 0:
            matches = []
            for t in f.league.teams.all():
                for p in t.active_players():
                    matches.append(Match(fixture=f, team=t, player=p))
            Match.objects.bulk_create(matches)

    @staticmethod
    @shared_task
    def check_winner(fixture_id):
        try:
            f = Fixture.objects.get(id=fixture_id)
            if not f.pools.all().exclude(state=Pool.STATE_SET).exists():
                w = f.get_winners()
                payload = { "$state": "winner" }
                send_push.delay([w.id], u"¡Felicidades! Has ganado la %s de la %s." % (f.name, f.league.name), payload)
        except Exception as e:
            print e

    def get_winners(self):
        lb = self.league.leaderboard(fixture=self)
        top_teams = filter(lambda t:t.points==lb[0].points, lb)
        top_players = []
        for t in top_teams:
            tlb = self.league.team_leaderboard(t, fixture=self)
            top_players += filter(lambda p:p.points==tlb[0].points, tlb)
        max_points = max(pl.points for pl in top_players)
        return list(set(filter(lambda p:p.points==max_points, top_players))) #Removing dupes

    def get_players(self):
        return get_user_model().objects.filter(matches=Match.objects.filter(fixture=self, played__gt=0)).distinct()

    def get_forecasts(self):
        return PoolResult.objects.filter(pool__fixtures=self).annotate(
            p=Count('players')).aggregate(Sum('p')).get('p__sum')

    def get_extras(self):
        m = Match.objects.filter(fixture=self).values('player', 'extra_points')
        return len(filter(lambda x: x.get('extra_points'),m))

    def __unicode__(self):
        if self.league:
            return "%s - %s" % (unicode(self.league.name), unicode(self.name))
        return unicode(self.name)

    class Meta:
        app_label = 'game'
        ordering = ['-league__name', '-end_date']


class Match(models.Model):
    EXTRA_TYPE_SHARE_FB = 'extra_type_share_fb'
    EXTRA_TYPE_RATE = 'extra_type_rate'
    EXTRA_TYPE_FEEDBACK = 'extra_type_feedback'
    EXTRA_TYPE_AD = 'extra_type_ad'
    EXTRA_TYPE_VISIT = 'extra_type_visit'
    EXTRA_TYPE_DOWNLOAD = 'extra_type_download'
    EXTRA_TYPE_CHOICES = (
        (EXTRA_TYPE_SHARE_FB, 'Share Facebook'),
        (EXTRA_TYPE_RATE, 'Rate'),
        (EXTRA_TYPE_FEEDBACK, 'Feedback'),
        (EXTRA_TYPE_AD, 'Watch Ad'),
        (EXTRA_TYPE_VISIT, 'Visit Website'),
        (EXTRA_TYPE_DOWNLOAD, 'Download'),
    )
    fixture = models.ForeignKey(Fixture, blank=True, null=True, related_name='matches')
    team = models.ForeignKey(Team, blank=True, null=True, related_name='matches')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='matches')
    played = models.IntegerField(default=0) #Number of pools played
    score = models.IntegerField(default=0)
    extra_points = models.BooleanField(default=False)
    extra_type = models.CharField(max_length=255, blank=True, null=True, choices=EXTRA_TYPE_CHOICES)
    extra_data = models.TextField(blank=True, null=True)
    extra_date = models.DateTimeField(blank=True, null=True)

    @staticmethod
    def clean(f):
        #See also: http://stackoverflow.com/questions/8989221/django-select-only-rows-with-duplicate-field-values
        for t in Team.objects.all():
            pp = [m.player for m in Match.objects.filter(fixture=f, team=t)]
            gar = set(pp) - set(t.active_players())
            for g in gar:
                Match.objects.filter(fixture=f, player=g, team=t).delete()

    def __unicode__(self):
        return "%s - %s - %s: %s" % (unicode(self.player), unicode(self.team), unicode(self.fixture), unicode(self.score))

    class Meta:
        app_label = 'game'
