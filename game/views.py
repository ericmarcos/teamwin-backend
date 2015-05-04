from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import detail_route, list_route

from users.models import get_fb_friends
from .models import *
from .permissions import *
from .serializers import *


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [TeamPermission,]

    def get_queryset(self):
        if self.request.DATA.get('friends'):
            friends = get_fb_friends(self.request.user)
            return Team.objects.filter(players=friends).exclude(players=self.request.user).distinct()
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
            return Response({'detail': str(e)},
                status=status.HTTP_406_NOT_ACCEPTABLE)
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
        user = get_user_model().objects.get(id=request.DATA.get('user_id'))
        try:
            sign = team.sign(user)
        except Exception as e:
            return Response({'detail': str(e)},
                status=status.HTTP_406_NOT_ACCEPTABLE)
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
        user = get_user_model().objects.get(id=request.DATA.get('user_id'))
        try:
            team.fire(user)
        except Exception as e:
            return Response({'detail': str(e)},
                status=status.HTTP_406_NOT_ACCEPTABLE)
        return Response({'status': 'Player %s was fired' % user.id})

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def leave(self, request, pk=None):
        team = self.get_object()
        try:
            team.fire(request.user)
        except Exception as e:
            return Response({'detail': str(e)},
                status=status.HTTP_406_NOT_ACCEPTABLE)
        return Response({'status': 'You left the team %s' % team.id})


class PoolViewSet(viewsets.ModelViewSet):
    queryset = Pool.objects.all()
    serializer_class = PoolSerializer
