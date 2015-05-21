from django.conf import settings
from django.http import Http404
from django.contrib.auth import get_user_model
from rest_framework import serializers, exceptions, status, pagination

from .models import *


class PoolOptionSerializer(serializers.ModelSerializer):
    pic = serializers.ReadOnlyField(source='get_pic_url')

    class Meta:
        model = PoolOption
        fields = ('name', 'pic', )


class PoolSerializer(serializers.HyperlinkedModelSerializer):
    options = PoolOptionSerializer(many=True, read_only=True)
    league = serializers.SerializerMethodField()
    fixture = serializers.SerializerMethodField()

    def get_league(self, pool):
        fixture = pool.fixtures.first()
        if fixture and fixture.league:
            return fixture.league.name
        return "Unknown League"

    def get_fixture(self, pool):
        fixture = pool.fixtures.first()
        if fixture:
            return fixture.name
        return "Unknown Fixture"

    class Meta:
        model = Pool
        fields = ('url', 'id', 'title','created_at','closing_date','pool_type','public','state','options', 'league', 'fixture')


class UserSerializer(serializers.ModelSerializer):
    pic = serializers.SerializerMethodField()

    def get_pic(self, user):
        return user.profile.get_profile_pic_url()

    class Meta:
        model = get_user_model()
        fields = ('id', 'username','pic',)


class UserFullSerializer(serializers.ModelSerializer):
    pic = serializers.SerializerMethodField()
    friends = serializers.SerializerMethodField()

    def get_friends(self, user):
        friends = [profile.user for profile in user.profile.friends.all()]
        return UserSerializer(friends, many=True, context=self.context).data

    def get_pic(self, user):
        return user.profile.get_profile_pic_url()

    class Meta:
        model = get_user_model()
        fields = ('id', 'username','pic', 'friends')


class TeamLeaderboardSerializer(serializers.ModelSerializer):
    pic = serializers.SerializerMethodField()
    points = serializers.IntegerField()
    played = serializers.IntegerField()
    did_share = serializers.BooleanField()

    def get_pic(self, user):
        return user.profile.get_profile_pic_url()

    class Meta:
        model = get_user_model()
        fields = ('id', 'username','pic', 'points', 'played', 'did_share')


class TeamLeagueSerializer(serializers.ModelSerializer):
    leaderboard = serializers.SerializerMethodField()
    prev_leaderboard = serializers.SerializerMethodField()

    def get_leaderboard(self, league):
        leaderboard = league.team_leaderboard(self.context['view'].get_object())
        return TeamLeaderboardSerializer(leaderboard, many=True, context=self.context).data

    def get_prev_leaderboard(self, league):
        leaderboard = league.team_leaderboard(self.context['view'].get_object(), prev=1)
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
    leagues = TeamLeagueSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ('url', 'id', 'name','pic','players','players_waiting_captain','players_pending','captain', 'leagues')


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
    prizes = PrizeSerializer(many=True, read_only=True)

    def get_leaderboard(self, league):
        user = self.context['request'].user if self.context['request'].user.is_authenticated() else None
        leaderboard = league.leaderboard(user=user)
        return LeagueLeaderboardSerializer(leaderboard, many=True, context=self.context).data

    class Meta:
        model = League
        fields = ('url', 'id', 'name','pic','description','leaderboard', 'prizes',)
