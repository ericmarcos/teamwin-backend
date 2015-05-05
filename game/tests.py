import json
#from mock import Mock
#from celery import current_app as celery
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
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

        self.username_1 = 'test_user_1'
        self.email_1 = 'test_user_1@dareyoo.net'
        self.password_1 = 'pass'
        self.user_1 = get_user_model().objects.create_user(self.username_1, self.email_1, self.password_1)
        self.user_1.profile = DareyooUserProfile(user_id=self.user_1.id)
        self.user_1.profile.save()

        self.username_2 = 'test_user_2'
        self.email_2 = 'test_user_2@dareyoo.net'
        self.password_2 = 'pass'
        self.user_2 = get_user_model().objects.create_user(self.username_2, self.email_2, self.password_2)
        self.user_2.profile = DareyooUserProfile(user_id=self.user_2.id)
        self.user_2.profile.save()

        self.username_3 = 'test_user_3'
        self.email_3 = 'test_user_3@dareyoo.net'
        self.password_3 = 'pass'
        self.user_3 = get_user_model().objects.create_user(self.username_3, self.email_3, self.password_3)
        self.user_3.profile = DareyooUserProfile(user_id=self.user_3.id)
        self.user_3.profile.save()

        self.username_4 = 'test_user_4'
        self.email_4 = 'test_user_4@dareyoo.net'
        self.password_4 = 'pass'
        self.user_4 = get_user_model().objects.create_user(self.username_4, self.email_4, self.password_4)
        self.user_4.profile = DareyooUserProfile(user_id=self.user_4.id)
        self.user_4.profile.save()

        self.username_5 = 'test_user_5'
        self.email_5 = 'test_user_5@dareyoo.net'
        self.password_5 = 'pass'
        self.user_5 = get_user_model().objects.create_user(self.username_5, self.email_5, self.password_5)
        self.user_5.profile = DareyooUserProfile(user_id=self.user_5.id)
        self.user_5.profile.save()

    def test_league_leaderboard(self):

        ###### Creating team with user 1
        self.client.force_authenticate(user=self.user_1)

        team_count = Team.objects.count()
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

        team.delete()
        self.client.force_authenticate(user=None)
