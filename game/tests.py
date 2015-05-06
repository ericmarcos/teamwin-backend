import json
#from mock import Mock
#from celery import current_app as celery
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
#from django.test.utils import override_settings
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import *
from .models import *


class LeagueResourceTest(APITestCase):
    # Use ``fixtures`` & ``urls`` as normal. See Django's ``TestCase``
    # documentation for the gory details.
    #fixtures = ['test_data.json']

    def future(self, minutes=0):
        return timezone.now() + timezone.timedelta(minutes=minutes)

    def time_machine(self, minutes=0):
        if not getattr(self, 'original_now', False):
            self.original_now = timezone.now
        timezone.now = lambda: self.original_now() + timezone.timedelta(minutes=minutes)

    def setUp(self):
        super(LeagueResourceTest, self).setUp()

        #celery.send_task = Mock()

        self.user_1 = self.create_user('test_user_1')
        self.user_2 = self.create_user('test_user_2')
        self.user_3 = self.create_user('test_user_3')
        self.user_4 = self.create_user('test_user_4')
        self.user_5 = self.create_user('test_user_5')

    def create_user(self, username):
        user = get_user_model().objects.create_user(username, '%s@dy.com' % username, '1234')
        user.profile = DareyooUserProfile(user_id=user.id)
        user.profile.save()
        return user

    def test_team_creation(self):
        ###### Creating team with user 1
        self.client.force_authenticate(user=self.user_1)

        team_count = Team.objects.count()
        
        ###### Creating a team
        post_data = {
            'name': 'Team1',
        }
        url = reverse('team-list')
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.count(), team_count + 1)

        team = Team.objects.last()
        self.assertEqual(team.name, post_data.get('name'))
        self.assertEqual(team.players.count(), 1)
        self.assertTrue(team.is_captain(self.user_1))

        ###### Testing team creation limit
        for i in xrange(settings.DAREYOO_MAX_TEAMS - 1):
            response = self.client.post(url, post_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Team.objects.count(), team_count + settings.DAREYOO_MAX_TEAMS)

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        Team.objects.all().delete()
        self.client.force_authenticate(user=None)

    def test_team_participation(self):
        t = Team.objects.create(name='t1')
        t.set_captain(self.user_1)

        ###### Joining team with user 2
        self.client.force_authenticate(user=self.user_2)
        url = reverse('team-request-enroll', args=(t.id,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.waiting_captain().count(), 1)

        ###### User 1 declines request
        self.client.force_authenticate(user=self.user_1)
        url = reverse('team-fire', args=(t.id,))
        response = self.client.post(url, {'user_id': self.user_2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.waiting_captain().count(), 0)

        ###### Joining team with user 2 (again)
        self.client.force_authenticate(user=self.user_2)
        url = reverse('team-request-enroll', args=(t.id,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.waiting_captain().count(), 1)

        ###### User 1 accepts request
        self.client.force_authenticate(user=self.user_1)
        url = reverse('team-sign', args=(t.id,))
        response = self.client.post(url, {'user_id': self.user_2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.active_players().count(), 2)

        ###### User 1 fires user 2
        self.client.force_authenticate(user=self.user_1)
        url = reverse('team-fire', args=(t.id,))
        response = self.client.post(url, {'user_id': self.user_2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.active_players().count(), 1)

        ###### User 1 signs user 2
        self.client.force_authenticate(user=self.user_1)
        url = reverse('team-sign', args=(t.id,))
        response = self.client.post(url, {'user_id': self.user_2.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.waiting_players().count(), 1)

        ###### User 2 accepts request
        self.client.force_authenticate(user=self.user_2)
        url = reverse('team-request-enroll', args=(t.id,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.active_players().count(), 2)

        ###### User 2 leaves team
        self.client.force_authenticate(user=self.user_2)
        url = reverse('team-leave', args=(t.id,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.active_players().count(), 1)

        ###### Testing players limit

        #Team should be able to get "infinite" requests
        url = reverse('team-request-enroll', args=(t.id,))
        for i in xrange(settings.DAREYOO_MAX_PLAYERS * 2):
            player = self.create_user('player%s' % i)
            self.client.force_authenticate(user=player)
            response = self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.waiting_captain().count(), settings.DAREYOO_MAX_PLAYERS * 2)
        self.assertEqual(t.active_players().count(), 1)

        #But should only be able to accept DAREYOO_MAX_PLAYERS requests
        self.client.force_authenticate(user=self.user_1)
        url = reverse('team-sign', args=(t.id,))
        for i, player in enumerate(t.waiting_captain()):
            response = self.client.post(url, {'user_id': player.id})
            if i < settings.DAREYOO_MAX_PLAYERS - 1:
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(t.active_players().count(), 2 + i)
            else:
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(t.active_players().count(), settings.DAREYOO_MAX_PLAYERS)

        Membership.objects.filter(team=t, is_captain=False).delete()

        #Captain should be able to sign "infinite" players
        url = reverse('team-sign', args=(t.id,))
        self.client.force_authenticate(user=self.user_1)
        for i in xrange(settings.DAREYOO_MAX_PLAYERS * 2):
            response = self.client.post(url, {'user_id': get_user_model().objects.get(username='player%s' % i).id})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(t.waiting_players().count(), settings.DAREYOO_MAX_PLAYERS * 2)
        self.assertEqual(t.active_players().count(), 1)

        #But only DAREYOO_MAX_PLAYERS should be able to accept the request
        url = reverse('team-request-enroll', args=(t.id,))
        for i, player in enumerate(t.waiting_captain()):
            self.client.force_authenticate(user=player)
            response = self.client.post(url)
            if i < settings.DAREYOO_MAX_PLAYERS - 1:
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(t.active_players().count(), 2 + i)
            else:
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(t.active_players().count(), settings.DAREYOO_MAX_PLAYERS)

        get_user_model().objects.filter(username__contains='player').delete()

        Team.objects.all().delete()
        self.client.force_authenticate(user=None)

    def test_league_participation(self):
        l = League.objects.create(name='l1')

        t = Team.objects.create(name='t1')
        t.set_captain(self.user_1)
        Membership.objects.create(team=t, player=self.user_2)

        ###### Shouldn't be able to join the lague with user 3 nor user 2
        self.client.force_authenticate(user=self.user_3)
        url = reverse('league-enroll', args=(l.id,))
        response = self.client.post(url, {'team_id': t.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(l.teams.count(), 0)
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(url, {'team_id': t.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(l.teams.count(), 0)
        # But should be able to join with user 1 (captain)
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(url, {'team_id': t.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(l.teams.count(), 1)

        ###### Shouldn't be able to leave the lague with user 3 nor user 2
        self.client.force_authenticate(user=self.user_3)
        url = reverse('league-leave', args=(l.id,))
        response = self.client.post(url, {'team_id': t.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(l.teams.count(), 1)
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(url, {'team_id': t.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(l.teams.count(), 1)
        # But should be able to leave with user 1 (captain)
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(url, {'team_id': t.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(l.teams.count(), 0)
