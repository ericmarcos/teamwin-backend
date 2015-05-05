from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ParseError

from .models import *
from .permissions import *
from .serializers import *


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = [TeamPermission,]

    def get_serializer_class(self):
        if self.action == 'list':
            return TeamShortSerializer
        return TeamSerializer

    def get_queryset(self):
        if self.request.query_params.get('friends'):
            return Team.objects.friends(self.request.user)
        else:
            return self.request.user.teams.all()

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
        user = get_user_model().objects.get(id=request.data.get('user_id'))
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
        user = get_user_model().objects.get(id=request.data.get('user_id'))
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


class PoolViewSet(viewsets.ModelViewSet):
    serializer_class = PoolSerializer
    permission_classes = [PoolPermission, ]

    
    def get_queryset(self):
        if self.request.query_params.get('pending'):
            return Pool.objects.pending(self.request.user)
        elif self.request.query_params.get('played'):
            return Pool.objects.played(self.request.user)
        else:
            return Pool.objects.public()

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated,])
    def play(self, request, pk=None):
        pool = self.get_object()
        try:
            result = request.data['result']
            pool.play(request.user, result)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'Result %s played for pool %s' % (result, pool)})

    @detail_route(methods=['post'])
    def set(self, request, pk=None):
        pool = self.get_object()
        try:
            result = request.data['result']
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
            team_id = request.data['team_id']
            league.enroll(request.user, team_id)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'Team %s was successfully enrolled to %s' % (team_id, league)})

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated,])
    def leave(self, request, pk=None):
        league = self.get_object()
        try:
            team_id = request.data['team_id']
            league.leave(request.user, team_id)
        except Exception as e:
            raise ParseError(detail=str(e))
        return Response({'status': 'Team %s left the league %s' % (team_id, league)})
