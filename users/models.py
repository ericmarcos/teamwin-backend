import collections
import urllib2
import base64
import json
import requests
from celery import shared_task
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone


def get_default_profile_pic(user_id):
    return settings.DEFAULT_PROFILE_PIC_URL % ((user_id or 1) % 10)


def get_fb_friends(user):
    social_user = user.social_auth.filter(
        provider='facebook',
    ).first()
    if social_user:
        url = u'https://graph.facebook.com/{0}/' \
              u'friends?fields=id,name,picture' \
              u'&access_token={1}'.format(
                  social_user.uid,
                  social_user.extra_data['access_token'],
              )
        resp = requests.get(url)
        resp.raise_for_status()
        resp = resp.json()
        friends = resp['data']
        while 'paging' in resp and 'next' in resp['paging']:
            resp = requests.get(resp['paging']['next']).json()
            friends.extend(resp['data'])
        uids = [f['id'] for f in friends]
        in_app_friends = get_user_model().objects.filter(social_auth__uid__in=uids, social_auth__provider='facebook')
        return in_app_friends
    return []


@shared_task
def send_push(users_ids, text, payload=None):
    tokens = [u.devices.first().token for u in get_user_model().objects.filter(id__in=users_ids) if u.devices.count() > 0]
    if tokens:
        post_data = {
            'tokens': tokens,
            'notification': {
                'alert': text,
            }
        }
        if payload:
            post_data['notification']['android'] = {'payload':payload}
            post_data['notification']['ios'] = {'payload':payload}
        app_id = settings.IONIC_APP_ID
        private_key = settings.IONIC_API_KEY
        url = "https://push.ionic.io/api/v1/push"
        req = urllib2.Request(url, data=json.dumps(post_data))
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Ionic-Application-Id", app_id)
        b64 = base64.encodestring('%s:' % private_key).replace('\n', '')
        req.add_header("Authorization", "Basic %s" % b64)
        resp = urllib2.urlopen(req)
        return resp


class DareyooUserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile')
    ionic_id = models.CharField(max_length=255, blank=True, null=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='users_invited')
    campaign = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='profiles', null=True, blank=True)
    gender = models.CharField(max_length=255, blank=True, null=True)
    locale = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    timezone = models.CharField(max_length=255, blank=True, null=True)
    friends = models.ManyToManyField("self", blank=True)
    is_pro = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)

    def get_profile_pic_url(self):
        if self.pic:
            return self.pic._get_url().split('?')[0]
        else:
            return get_default_profile_pic(self.user.id)

    def add_friend(self, user):
        '''
        Can take a single user or a list of users
        '''
        if isinstance(user, collections.Iterable):
            try:
                self.friends.add(*[u.profile for u in user])
            except:
                self.friends.add(*user)
        else:
            try:
                self.friends.add(user.profile)
            except:
                self.friends.add(user)

    def __unicode__(self):
        return "%s - %s" % (self.user.email, self.user.username)


class Device(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='devices')
    token = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return "%s - %s" % (self.user.username, self.token)


class UserActivation(models.Model):
    LEVEL_LOGIN = 1
    LEVEL_PARTICIPATE = 2
    LEVEL_CREATE = 3
    LEVEL_BUY = 4

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="activations", blank=True, null=True) 
    timestamp = models.DateTimeField()
    level = models.IntegerField(blank=True, null=True, default=1)

    def __unicode__(self):
        return "%s - %s - %s" % (self.timestamp, self.user.username, self.level)

    @staticmethod
    @shared_task
    def new_activation(user, level=1, timestamp=None):
        now = timestamp or timezone.now()
        last_activation = user.activations.filter(level=level).order_by("-timestamp").first()
        if not last_activation or last_activation.timestamp < now - timedelta(hours=1):
            UserActivation.objects.create(user=user, timestamp=now, level=level)

    @staticmethod
    @shared_task
    def login(user):
        UserActivation.new_activation(user, UserActivation.LEVEL_LOGIN)
    
    @staticmethod
    @shared_task
    def participate(user):
        UserActivation.new_activation(user, UserActivation.LEVEL_PARTICIPATE)

    @staticmethod
    @shared_task
    def create(user):
        UserActivation.new_activation(user, UserActivation.LEVEL_CREATE)

    @staticmethod
    @shared_task
    def buy(user):
        UserActivation.new_activation(user, UserActivation.LEVEL_BUY)
