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

    class Meta:
        model = Pool
        fields = ('url', 'id', 'title','created_at','closing_date','pool_type','public','state','options')


class UserSerializer(serializers.ModelSerializer):
    pic = serializers.SerializerMethodField('get_profile_pic')

    def get_profile_pic(self, obj):
        return obj.profile.get_profile_pic_url()

    class Meta:
        model = get_user_model()
        fields = ('id', 'username','pic',)


class TeamLeagueSerializer(serializers.ModelSerializer):
    leaderboard = serializers.SerializerMethodField()
    prev_leaderboard = serializers.SerializerMethodField()

    def get_leaderboard(self, league):
        return league.team_leaderboard(self.context['view'].get_object())

    def get_prev_leaderboard(self, league):
        return league.team_leaderboard(self.context['view'].get_object(), prev=1)

    class Meta:
        model = League
        fields = ('name', 'leaderboard', 'prev_leaderboard', )


class TeamShortSerializer(serializers.HyperlinkedModelSerializer):
    pic = serializers.ReadOnlyField(source='get_pic_url')
    players = UserSerializer(many=True, source='active_players', read_only=True)
    captain = UserSerializer(read_only=True)

    class Meta:
        model = Team
        fields = ('url', 'id', 'name','pic','players','captain',)


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
