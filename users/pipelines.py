import requests as r
from celery import shared_task
import mailchimp
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import DareyooUserProfile, get_fb_friends, send_push


def save_profile(backend, user, response, *args, **kwargs):
    if user and backend.name == 'facebook' and kwargs.get('is_new'):
        try:
            user.profile
        except:
            user.profile = DareyooUserProfile(user_id=user.id)
        user.profile.gender = response.get('gender')
        user.profile.locale = response.get('locale')
        user.profile.location = response.get('location')
        user.profile.timezone = response.get('timezone')
        user.profile.save()
        try:
            register_email_mailchimp.delay(user.id)
        except:
            register_email_mailchimp(user.id)


#http://stackoverflow.com/questions/19890824/save-facebook-profile-picture-in-model-using-python-social-auth
def save_profile_picture(backend, user, response, *args, **kwargs):
    if user and  backend.name == 'facebook' and kwargs.get('is_new'):
        url = 'http://graph.facebook.com/{0}/picture'.format(response['id'])
        params = {'type': 'normal', 'height': 200, 'width': 200}
        try:
            resp = r.get(url, params=params)
            resp.raise_for_status()
            ext = "jpg" if resp.headers['content-type'] == 'image/jpeg' else 'png'
            user.profile.pic.save('{0}_social.{1}'.format(user.id, ext), ContentFile(resp.content))
            user.profile.save()
        except Exception as e:
            pass


def save_friends(backend, user, response, *args, **kwargs):
    if user and  backend.name == 'facebook' and kwargs.get('is_new'):
        try:
            friends = get_fb_friends(user)
            user.profile.add_friend(friends)
            if user.profile.gender == 'female' or user.profile.gender == 'mujer':
                msg = 'Tu amiga %s acaba de unirse a Teamwin.' % (user.first_name or user.username)
            else:
                msg = 'Tu amigo %s acaba de unirse a Teamwin.' % (user.first_name or user.username)
            send_push.delay([f.id for f in friends], msg)
        except Exception as e:
            pass

@shared_task
def register_email_mailchimp(user_id):
    user = get_user_model().objects.get(id=user_id)
    if user and user.email:
        try:
            m = mailchimp.Mailchimp(settings.MAILCHIMP_API_KEY)
            list_id = settings.MAILCHIMP_LISTS.get('Teamwin')
            merge_vars = {'FNAME': user.first_name, 'LNAME': user.last_name}
            m.lists.subscribe(list_id, {'email': user.email}, merge_vars, double_optin=False)
        except Exception as e:
            print e
