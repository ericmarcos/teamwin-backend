from django.conf.urls import url, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'teams', TeamViewSet, base_name='team')
router.register(r'pools', PoolViewSet, base_name='pool')
router.register(r'leagues', LeagueViewSet, base_name='league')
router.register(r'users', UserViewSet, base_name='user')

urlpatterns = [
    url(r'^', include(router.urls)),
]
