from django.apps import AppConfig
from django.contrib.auth import get_user_model

from .models import get_user_points, get_user_played, get_user_extra_points


class GameConfig(AppConfig):
    name = 'game'

    def ready(self):
        u = get_user_model()
        u.points = property(get_user_points)
        u.played = property(get_user_played)
        u.extra_points = property(get_user_extra_points)