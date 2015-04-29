import requests as r

from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import DareyooUserProfile


def save_profile(backend, user, response, *args, **kwargs):
    if user and backend.name == 'facebook':
        try:
            user.profile
        except:
            user.profile = DareyooUserProfile(user_id=user.id)
        user.profile.gender = response.get('gender')
        user.profile.locale = response.get('locale')
        user.profile.location = response.get('location')
        user.profile.timezone = str(response.get('timezone'))
        user.profile.save()


#http://stackoverflow.com/questions/19890824/save-facebook-profile-picture-in-model-using-python-social-auth
def save_profile_picture(backend, user, response, *args, **kwargs):
    if user and  backend.name == 'facebook':
        url = 'http://graph.facebook.com/{0}/picture'.format(response['id'])
        params = {'type': 'normal', 'height': 200, 'width': 200}
        try:
            resp = r.get(url, params=params)
            resp.raise_for_status()
            ext = "jpg" if resp.headers['content-type'] == 'image/jpeg' else 'png'
            user.profile.pic.save('{0}_social.{1}'.format(user.id, ext), ContentFile(resp.content))
            user.profile.save()
        except Exception as e:
            print e
