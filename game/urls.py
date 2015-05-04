from django.conf.urls import url, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'teams', TeamViewSet, base_name='team')
router.register(r'pools', PoolViewSet, base_name='pool')

urlpatterns = [
    url(r'^', include(router.urls)),
]
