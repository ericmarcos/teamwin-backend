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

        Team.objects.all().delete()
        League.objects.all().delete()
        self.client.force_authenticate(user=None)

    def test_pool_participation(self):
        l = League.objects.create(name='l1')

        t = Team.objects.create(name='t1')
        t.set_captain(self.user_1)
        Membership.objects.create(team=t, player=self.user_2)

        self.user_5.is_staff = True
        self.user_5.save()

        p = Pool.objects.create()

        ###### Shouldn't be able to play when the pool is in draft
        url = reverse('pool-play', args=(p.id,))
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(p.players().count(), 0)
        # Neither set the bet
        url = reverse('pool-set', args=(p.id,))
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        p.publish()

        ###### Now the bet is open, should be able to play
        url = reverse('pool-play', args=(p.id,))
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(p.players().count(), 1)
        # Playing twice should have no effect
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(p.players().count(), 1)
        # Playing with another user for same result
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(p.players().count(), 2)
        self.assertEqual(p.results.count(), 1)
        # Playing with another user for another result
        self.client.force_authenticate(user=self.user_3)
        response = self.client.post(url, {'result': 'X'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(p.players().count(), 3)
        self.assertEqual(p.results.count(), 2)
        
        # User 1 shouldn't be able to set the bet
        url = reverse('pool-set', args=(p.id,))
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # But user 5 (staff) should have no problem
        self.client.force_authenticate(user=self.user_5)
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(p.winners().count(), 2)
        # Can't set it again
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Now that it's closed, shouldn't be able to play again
        url = reverse('pool-play', args=(p.id,))
        self.client.force_authenticate(user=self.user_4)
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(p.players().count(), 3)

        ###### Same flow but with closing step
        p.delete()
        p = Pool.objects.create()
        self.client.force_authenticate(user=self.user_1)
        p.publish()
        url = reverse('pool-play', args=(p.id,))
        self.client.post(url, {'result': '1'})
        p.close()
        # Shouldn't be able to play
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(url, {'result': '1'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user_5.is_staff = False
        self.user_5.save()
        Team.objects.all().delete()
        League.objects.all().delete()
        Pool.objects.all().delete()
        self.client.force_authenticate(user=None)

    def test_leaderboards(self):
        '''
        Full game test. We create 2 teams with 3 players each (2 shared players),
        1 league with 2 fixtures and 3 pools for each fixture. Then we play the
        pools, we set them and check that the generated leaderboards are ok.
        '''
        t1 = Team.objects.create(name='t1')
        t1.set_captain(self.user_1)
        Membership.objects.create(team=t1, player=self.user_3)
        Membership.objects.create(team=t1, player=self.user_4)

        t2 = Team.objects.create(name='t2')
        t2.set_captain(self.user_2)
        Membership.objects.create(team=t2, player=self.user_3)
        Membership.objects.create(team=t2, player=self.user_4)

        l = League.objects.create(name='l1')
        l.teams.add(t1)
        l.teams.add(t2)

        f1 = Fixture.objects.create(league=l, name='f1')
        f1.start_date = timezone.now() - timezone.timedelta(days=8)
        f1.end_date = timezone.now() - timezone.timedelta(days=1)
        f1.save()

        p11 = Pool.objects.create(title='p11', state=Pool.STATE_OPEN)
        p12 = Pool.objects.create(title='p12', state=Pool.STATE_OPEN)
        p13 = Pool.objects.create(title='p13', state=Pool.STATE_OPEN)
        f1.pools.add(p11, p12, p13)

        f2 = Fixture.objects.create(league=l, name='f2')
        f2.start_date = timezone.now() - timezone.timedelta(days=1)
        f2.end_date = timezone.now() + timezone.timedelta(days=6)
        f2.save()

        p21 = Pool.objects.create(title='p21', state=Pool.STATE_OPEN)
        p22 = Pool.objects.create(title='p22', state=Pool.STATE_OPEN)
        p23 = Pool.objects.create(title='p23', state=Pool.STATE_OPEN)
        f2.pools.add(p21, p22, p23)

        p11.play(self.user_1, "1")
        p12.play(self.user_1, "1")
        p13.play(self.user_1, "1")

        p11.play(self.user_2, "1")
        p12.play(self.user_2, "1")
        p13.play(self.user_2, "2")

        p11.play(self.user_3, "1")
        p12.play(self.user_3, "2")
        p13.play(self.user_3, "2")

        p11.play(self.user_4, "2")
        p12.play(self.user_4, "2")
        p13.play(self.user_4, "2")

        p11.set("1")
        p12.set("1")
        p13.set("1")

        #Checking general leaderboard. Team 1 should be first with 4 points
        #while team 2 should have 3 points
        rnk = l.leaderboard(1)
        self.assertEqual(rnk[0], t1)
        self.assertEqual(rnk[0].points, 4)
        self.assertEqual(rnk[1], t2)
        self.assertEqual(rnk[1].points, 3)
        #Team 1 leaderboard should be 1(user1, 3) - 2(user3, 1) - 3(user4, 0)
        rnk = l.team_leaderboard(t1, 1)
        self.assertEqual(rnk[0], self.user_1)
        self.assertEqual(rnk[0].points, 3)
        self.assertEqual(rnk[0].played, 3)
        self.assertEqual(rnk[1], self.user_3)
        self.assertEqual(rnk[1].points, 1)
        self.assertEqual(rnk[1].played, 3)
        self.assertEqual(rnk[2], self.user_4)
        self.assertEqual(rnk[2].points, 0)
        self.assertEqual(rnk[2].played, 3)
        #Team 2 leaderboard should be 1(user2, 2) - 2(user3, 1) - 3(user4, 0)
        rnk = l.team_leaderboard(t2, 1)
        self.assertEqual(rnk[0], self.user_2)
        self.assertEqual(rnk[0].points, 2)
        self.assertEqual(rnk[0].played, 3)
        self.assertEqual(rnk[1], self.user_3)
        self.assertEqual(rnk[1].points, 1)
        self.assertEqual(rnk[1].played, 3)
        self.assertEqual(rnk[2], self.user_4)
        self.assertEqual(rnk[2].points, 0)
        self.assertEqual(rnk[2].played, 3)

        p21.play(self.user_1, "1")
        p22.play(self.user_1, "1")

        p21.play(self.user_2, "1")
        p22.play(self.user_2, "1")
        p23.play(self.user_2, "2")

        p21.play(self.user_3, "1")
        p22.play(self.user_3, "2")
        p23.play(self.user_3, "2")

        p21.play(self.user_4, "2")
        p22.play(self.user_4, "2")

        p21.set("2")
        p22.set("1")
        p23.set("2")

        #Checking general leaderboard. Team 2 should be first with 4 points
        #while team 1 should have 3 points
        rnk = l.leaderboard()
        self.assertEqual(rnk[0], t2)
        self.assertEqual(rnk[0].points, 4)
        self.assertEqual(rnk[1], t1)
        self.assertEqual(rnk[1].points, 3)
        #Team 1 leaderboard is all tied to 1
        rnk = l.team_leaderboard(t1)
        #self.assertEqual(rnk[0], self.user_1)
        self.assertEqual(rnk[0].points, 1)
        #self.assertEqual(rnk[0].played, 3)
        #self.assertEqual(rnk[1], self.user_3)
        self.assertEqual(rnk[1].points, 1)
        #self.assertEqual(rnk[1].played, 3)
        #self.assertEqual(rnk[2], self.user_4)
        self.assertEqual(rnk[2].points, 1)
        #self.assertEqual(rnk[2].played, 3)
        #Team 2 leaderboard should be 1(user2, 2) - 2(user3, 1) - 3(user4, 1)
        rnk = l.team_leaderboard(t2)
        self.assertEqual(rnk[0], self.user_2)
        self.assertEqual(rnk[0].points, 2)
        self.assertEqual(rnk[0].played, 3)
        self.assertEqual(rnk[1], self.user_3)
        self.assertEqual(rnk[1].points, 1)
        self.assertEqual(rnk[1].played, 3)
        self.assertEqual(rnk[2], self.user_4)
        self.assertEqual(rnk[2].points, 1)
        self.assertEqual(rnk[2].played, 2)

        Team.objects.all().delete()
        League.objects.all().delete()
        self.client.force_authenticate(user=None)
