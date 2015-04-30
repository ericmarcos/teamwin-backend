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


class PoolSerializer(serializers.ModelSerializer):
    pic = serializers.Field(source='get_pic_url')
    options = PoolOptionSerializer()

    class Meta:
        model = Pool
        fields = ('url','title','created_at','closing_date','pool_type','public','state','options')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    pic = serializers.SerializerMethodField('get_profile_pic')

    def get_profile_pic(self, obj):
        return obj.profile.get_profile_pic_url()

    class Meta:
        model = get_user_model()
        fields = ('username','pic',)


class TeamSerializer(serializers.ModelSerializer):
    pic = serializers.ReadOnlyField(source='get_pic_url')
    players = UserSerializer(many=True, source='active_players')
    players_waiting_captain = UserSerializer(many=True, source='waiting_captain')
    players_pending = UserSerializer(many=True, source='waiting_players')
    captain = UserSerializer()

    class Meta:
        model = Team
        fields = ('name','pic','players','players_waiting_captain','players_pending','captain')
