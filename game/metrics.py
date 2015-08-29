from datetime import timedelta
from django.utils import timezone
from .models import *


def day_cohorts(n=30, days=1):
    today = timezone.now().replace(second=59, minute=59, hour=23)
    return [today - timedelta(days=i) for i in xrange(0, n, days)]

def week_cohorts(n=16):
    today = timezone.now()
    monday = today.replace(second=0, minute=0, hour=0,
        day=today.day + 7 - today.weekday())
    return [monday - timedelta(weeks=i) for i in xrange(0, n)]

def user_cohorts(time_cohorts):
    diff = time_cohorts[0] - time_cohorts[1]
    return [get_user_model().objects.filter(date_joined__range=(
        d - diff, d)) for d in time_cohorts]

def growth(time_cohorts):
    return [u.count() for u in user_cohorts(time_cohorts)]

def daily_growth(n=30, days=1):
    dc = day_cohorts(n, days)
    return growth(dc)

def weekly_growth(n=16):
    wc = week_cohorts(n)
    return growth(wc)

def active_users(queryset, period):
    fixtures = Fixture.objects.filter(start_date__range=period)
    matches = Match.objects.filter(fixture=fixtures, played__gt=0)
    return queryset.filter(matches=matches).distinct()

def retention_cohort(queryset, time_cohorts, absolute=True):
    '''absolute=True: returns absolute numbers,
    else as a % of the total number of users'''
    diff = time_cohorts[0] - time_cohorts[1]
    rc = [active_users(queryset, (c - diff, c)).count() for c in time_cohorts]
    if absolute:
        return rc
    else:
        total = queryset.count()
        return [float(active) / total for active in rc]

def daily_retention_cohorts(n=30, days=1, absolute=True):
    dc = day_cohorts(n, days)
    uc = user_cohorts(dc)
    return [list(reversed(retention_cohort(u, dc, absolute)))[-i-1:]
        for i,u in enumerate(uc)]

def weekly_retention_cohorts(n=16, absolute=True):
    wc = week_cohorts(n)
    uc = user_cohorts(wc)
    return [list(reversed(retention_cohort(u, wc, absolute)))[-i-1:]
        for i,u in enumerate(uc)]
