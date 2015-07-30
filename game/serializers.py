from django.conf import settings
from django.http import Http404
from django.contrib.auth import get_user_model
from rest_framework import serializers, exceptions, status, pagination

from .models import *


class PoolOptionSerializer(serializers.ModelSerializer):
    pic = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    short_name = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    second_color = serializers.SerializerMethodField()

    def get_pic(self, option):
        try:
            return option.get_pic_url() or option.item.get_pic_url()
        except:
            return option.get_pic_url()

    def get_name(self, option):
        try:
            return option.name or option.item.name
        except:
            return option.name

    def get_short_name(self, option):
        try:
            return option.item.short_name
        except:
            return option.name

    def get_number(self, option):
        try:
            return option.item.number
        except:
            return None

    def get_color(self, option):
        try:
            return option.item.color
        except:
            return None

    def get_second_color(self, option):
        try:
            return option.item.second_color
        except:
            return None

    class Meta:
        model = PoolOption
        fields = ('name', 'pic', 'short_name', 'color', 'second_color', 'number')


class PoolSerializer(serializers.HyperlinkedModelSerializer):
    options = PoolOptionSerializer(many=True, read_only=True)
    league = serializers.SerializerMethodField()
    fixture = serializers.SerializerMethodField()
    user_result = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    def get_league(self, pool):
        try:
            return pool.fixtures.first().league.name
        except:
            return None

    def get_fixture(self, pool):
        try:
            return pool.fixtures.first().name
        except:
            return None

    def get_user_result(self, pool):
        try:
            return pool.results.filter(players=self.context['request'].user).first().name
        except:
            return None

    def get_result(self, pool):
        try:
            return pool.winner_result().name
        except:
            return None

    class Meta:
        model = Pool
        fields = ('url', 'id', 'title','created_at','closing_date','pool_type','public','state','options', 'league', 'fixture', 'user_result', 'result')


class UserSerializer(serializers.ModelSerializer):
    pic = serializers.SerializerMethodField()

    def get_pic(self, user):
        return user.profile.get_profile_pic_url()

    class Meta:
        model = get_user_model()
        fields = ('id', 'username','pic', 'first_name')


class UserFullSerializer(serializers.ModelSerializer):
    pic = serializers.SerializerMethodField()
    friends = serializers.SerializerMethodField()
    ionic_id = serializers.SerializerMethodField()
    device_token = serializers.SerializerMethodField()

    def get_friends(self, user):
        try:
            friends = [profile.user for profile in user.profile.friends.all()]
            return UserSerializer(friends, many=True, context=self.context).data
        except:
            return []

    def get_pic(self, user):
        try:
            return user.profile.get_profile_pic_url()
        except:
            return None

    def get_ionic_id(self, user):
        try:
            return user.profile.ionic_id
        except:
            return None

    def get_device_token(self, user):
        try:
            return user.devices.first().token
        except:
            return None

    class Meta:
        model = get_user_model()
        fields = ('id', 'ionic_id', 'username','pic', 'friends', 'device_token', 'first_name')


class TeamLeaderboardSerializer(serializers.ModelSerializer):
    pic = serializers.SerializerMethodField()
    points = serializers.IntegerField()
    played = serializers.IntegerField()
    extra_points = serializers.BooleanField()

    def get_pic(self, user):
        return user.profile.get_profile_pic_url()

    class Meta:
        model = get_user_model()
        fields = ('id', 'username','pic', 'points', 'played', 'extra_points', 'first_name')


class TeamLeagueSerializer(serializers.ModelSerializer):
    leaderboard = serializers.SerializerMethodField()
    prev_leaderboard = serializers.SerializerMethodField()

    def get_leaderboard(self, league):
        team = self.context.get('team') or self.context['view'].get_object()
        leaderboard = league.team_leaderboard(team)
        return TeamLeaderboardSerializer(leaderboard, many=True, context=self.context).data

    def get_prev_leaderboard(self, league):
        team = self.context.get('team') or self.context['view'].get_object()
        leaderboard = league.team_leaderboard(team, prev=1)
        return TeamLeaderboardSerializer(leaderboard, many=True, context=self.context).data

    class Meta:
        model = League
        fields = ('name', 'leaderboard', 'prev_leaderboard', )


class TeamShortSerializer(serializers.HyperlinkedModelSerializer):
    pic = serializers.ReadOnlyField(source='get_pic_url')
    players = UserSerializer(many=True, source='active_players', read_only=True)
    captain = UserSerializer(read_only=True)
    state = serializers.SerializerMethodField()

    def get_state(self, team):
        user = self.context['request'].user if self.context['request'].user.is_authenticated() else None
        return team.get_state(user)

    class Meta:
        model = Team
        fields = ('url', 'id', 'name','pic','players','captain', 'state',)


class TeamSerializer(serializers.HyperlinkedModelSerializer):
    pic = serializers.ReadOnlyField(source='get_pic_url')
    players = UserSerializer(many=True, source='active_players', read_only=True)
    players_waiting_captain = UserSerializer(many=True, source='waiting_captain', read_only=True)
    players_pending = UserSerializer(many=True, source='waiting_players', read_only=True)
    captain = UserSerializer(read_only=True)
    leagues = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()

    def get_leagues(self, team):
        self.context['team'] = team
        return TeamLeagueSerializer(team.leagues.all(), many=True, context=self.context).data

    def get_state(self, team):
        user = self.context['request'].user if self.context['request'].user.is_authenticated() else None
        return team.get_state(user)

    class Meta:
        model = Team
        fields = ('url', 'id', 'name','pic','players','players_waiting_captain','players_pending','captain', 'leagues', 'state')


class LeagueLeaderboardSerializer(serializers.HyperlinkedModelSerializer):
    pic = serializers.ReadOnlyField(source='get_pic_url')
    captain = UserSerializer(read_only=True)
    points = serializers.IntegerField()

    class Meta:
        model = Team
        fields = ('url', 'id', 'name','pic','captain', 'points')


class PrizeSerializer(serializers.HyperlinkedModelSerializer):
    pic = serializers.ReadOnlyField(source='get_pic_url')

    class Meta:
        model = Prize
        fields = ('name', 'description', 'pic')

class LeagueSerializer(serializers.HyperlinkedModelSerializer):
    pic = serializers.ReadOnlyField(source='get_pic_url')
    leaderboard = serializers.SerializerMethodField()
    prev_leaderboard = serializers.SerializerMethodField()
    prizes = PrizeSerializer(many=True, read_only=True)
    pools = serializers.SerializerMethodField()
    prev_pools = serializers.SerializerMethodField()

    def get_leaderboard(self, league):
        user = self.context['request'].user if self.context['request'].user.is_authenticated() else None
        leaderboard = league.leaderboard(user=user)
        return LeagueLeaderboardSerializer(leaderboard, many=True, context=self.context).data

    def get_prev_leaderboard(self, league):
        user = self.context['request'].user if self.context['request'].user.is_authenticated() else None
        leaderboard = league.leaderboard(user=user, prev=1)
        return LeagueLeaderboardSerializer(leaderboard, many=True, context=self.context).data

    def get_pools(self, league):
        return league.pools().count()

    def get_prev_pools(self, league):
        return league.pools(prev=1).count()

    class Meta:
        model = League
        fields = ('url', 'id', 'name','pic','description','leaderboard','prev_leaderboard', 'prizes', 'pools', 'prev_pools')
