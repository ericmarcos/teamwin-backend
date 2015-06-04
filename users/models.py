import collections
import urllib2
import base64
import json

import requests
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model


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


def send_push(users, text, payload=None):
    tokens = [u.devices.first().token for u in users if u.devices.first()]
    post_data = {
        'tokens': tokens,
        'notification': {
            'alert': text,
            #'android': { 'payload': payload },
            #'ios': { 'payload': payload }
        }
    }
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
