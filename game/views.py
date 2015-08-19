# -*- coding: utf-8 -*-

import time
import boto
from boto.file.key import Key
from django.contrib.auth import get_user_model
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from django.conf import settings
from users.models import *
from .models import *
from .permissions import *
from .serializers import *

from rest_framework.authentication import SessionAuthentication

class CSRFExcemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated,]
    queryset = get_user_model().objects.all()

    def get_queryset(self):
        if self.action == 'list':
            return get_user_model().objects.filter(id=self.request.user.id)
        elif self.action == 'delete':
            return get_user_model().objects.none()
        return get_user_model().objects.all()

    def get_serializer_class(self):
        return UserSerializer

    @list_route(methods=['GET', 'POST'])
    def me(self, request, pk=None):
        if request.method == 'GET':
            return Response(UserFullSerializer(request.user).data)
        else:
            ionic_id = request.data.get('ionic_id')
            if ionic_id:
                DareyooUserProfile.objects.filter(user=request.user).update(ionic_id=ionic_id)
            device_token = request.data.get('device_token')
            device = request.user.devices.first()
            if device_token:
                if not device:
                    Device.objects.create(user=request.user, token=device_token)
                elif device.token != device_token:
                    Device.objects.filter(user=request.user).update(token=device_token)
            return Response(UserFullSerializer(request.user).data)

    @list_route(methods=['POST'])
    def share_results(self, request, pk=None):
        #http://stackoverflow.com/questions/14346065/upload-image-available-at-public-url-to-s3-using-boto
        try:
            conn = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            bucket = conn.get_bucket(bucket_name)
            key_name = "app_shares/%s_results_%s.png" % (int(time.time()), request.user.id)
            k = bucket.new_key(key_name)
            k.set_contents_from_file(request.FILES['results'], {"Content-Type": 'image/png'})
            k.make_public()
            http_url = 'http://{bucket}.{host}/{key}'.format(
                host=conn.server_name(),
                bucket=bucket_name,
                key=key_name)
            return Response({"url": http_url})
        except Exception as e:
            raise ParseError(detail=str(e))


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = [TeamPermission,]

    def get_serializer_class(self):
        #if self.action == 'list':
        #    return TeamShortSerializer
        return TeamSerializer

    def get_queryset(self):
        if self.action in ['detail', 'request_enroll', 'sign', 'search']:
            return Team.objects.all()
        if self.request.query_params.get('friends', self.request.data.get('friends')):
            try:
                return Team.objects.friends(self.request.user)
            except Exception as e:
                raise ParseError(detail=str(e))
        elif self.request.query_params.get('pending', self.request.data.get('pending')):
            return self.request.user.teams.pending()
        elif self.action == 'list':
            return self.request.user.teams.active()
        else:
            return self.request.user.teams.all()

    def perform_create(self, serializer):
        try:
            check_user_limits(self.request.user)
            team = serializer.save()
            team.set_captain(self.request.user, check=False)
        except Exception as e:
            raise ParseError(detail=str(e))

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def search(self, request, pk=None):
        qs = self.get_queryset()
        name = request.query_params.get('name', request.data.get('name'))
        if name:
            qs.filter(name__icontains=name)
            return Response(TeamSerializer(qs, many=True).data)
        return Response([])

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def request_enroll(self, request, pk=None):
        '''
        When a player request to enter a team. If the captain of the team already
        sent him a sign request, the player becomes active right away. Else, the
        request is set to pending until the captain signs it.
        '''
        team = self.get_object()
        try:
            enroll = team.request_enroll(request.user)
        except Exception as e:
            raise ParseError(detail=str(e))
        if enroll == Membership.STATE_ACTIVE:
            resp = 'Request accepted. Current state is "Active player"'
        elif enroll == Membership.STATE_WAITING_CAPTAIN:
            resp = 'Request sent. Curent state is "Waiting for captain approval"'
        else:
            resp = 'Nothing changed'
        return Response({'status': resp})

    @detail_route(methods=['post'])
    def sign(self, request, pk=None):
        '''
        When the captain wants to sign a player to enter a team. If the player already
        sent him an enroll request, the player becomes active right away. Else, the request
        is set to pending until the player accepts it.
        '''
        team = self.get_object()
        user_id = request.query_params.get('user_id', request.data.get('user_id'))
        user = get_user_model().objects.get(id=user_id)
        try:
            sign = team.sign(user)
        except Exception as e:
            raise ParseError(detail=str(e))
        if sign == Membership.STATE_ACTIVE:
            resp = 'Request accepted. Current state is "Active player"'
        elif sign == Membership.STATE_WAITING_PLAYER:
            resp = 'Request sent. Curent state is "Waiting for player to accept"'
        else:
            resp = 'Nothing changed'
        return Response({'status': resp})

    @detail_route(methods=['post'])
    def fire(self, request, pk=None):
        team = self.get_object()
        user_id = request.query_params.get('user_id', request.data.get('user_id'))
        user = get_user_model().objects.get(id=user_id)
        try:
            team.fire(user)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'Player %s was fired' % user.id})

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def leave(self, request, pk=None):
        team = self.get_object()
        try:
            team.fire(request.user)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'You left the team %s' % team.id})

    @detail_route(methods=['post'])
    def upload_avatar(self, request, *args, **kwargs):
        team = self.get_object()
        ext = "jpg" if request.FILES['avatar'].content_type == 'image/jpeg' else 'png'
        request.FILES['avatar'].name = '{0}_team.{1}'.format(team.id, ext)
        team.pic = request.FILES['avatar']
        team.save()
        return Response({'status': 'Avatar uploaded successfully.', 'url': team.get_pic_url()})


class PoolViewSet(viewsets.ModelViewSet):
    serializer_class = PoolSerializer
    permission_classes = [PoolPermission, ]

    
    def get_queryset(self):
        if self.request.user.is_authenticated():
            if self.request.query_params.get('pending', self.request.data.get('pending')):
                return Pool.objects.pending(self.request.user)
            elif self.request.query_params.get('played', self.request.data.get('played')):
                return Pool.objects.played(self.request.user)
            elif self.request.query_params.get('current', self.request.data.get('current')):
                return Pool.objects.current(self.request.user)
        return Pool.objects.public()

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated,])
    def play(self, request, pk=None):
        pool = self.get_object()
        try:
            result = request.query_params.get('result', request.data.get('result'))
            pool.play(request.user, result)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'Result %s played for pool %s' % (result, pool)})

    @detail_route(methods=['post'], authentication_classes=[CSRFExcemptSessionAuthentication])
    def set(self, request, pk=None):
        pool = self.get_object()
        try:
            result = request.query_params.get('result', request.data.get('result'))
            pool.set(result)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'Result %s set for pool %s' % (result, pool)})


class LeagueViewSet(viewsets.ModelViewSet):
    serializer_class = LeagueSerializer
    permission_classes = [LeaguePermission, ]

    
    def get_queryset(self):
        return League.objects.visible()

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated,])
    def enroll(self, request, pk=None):
        league = self.get_object()
        try:
            team_id = request.query_params.get('team_id', request.data.get('team_id'))
            league.enroll(request.user, team_id)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'Team %s was successfully enrolled to %s' % (team_id, league)})

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated,])
    def leave(self, request, pk=None):
        league = self.get_object()
        try:
            team_id = request.query_params.get('team_id', request.data.get('team_id'))
            league.leave(request.user, team_id)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'Team %s left the league %s' % (team_id, league)})

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated,])
    def extra_points(self, request, pk=None):
        league = self.get_object()
        try:
            etype = request.query_params.get('type', request.data.get('type'))
            edata = request.query_params.get('data', request.data.get('data'))
            league.extra_points(request.user, etype, edata)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'User won +2 extra points'})
