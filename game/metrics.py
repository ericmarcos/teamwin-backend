import random
from datetime import timedelta
from itertools import chain
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
    return [get_user_model().objects.filter(profile__isnull=False, profile__is_pro=False,
        is_staff=False, date_joined__range=(d - diff, d)) for d in time_cohorts]

def team_cohorts(time_cohorts):
    diff = time_cohorts[0] - time_cohorts[1]
    return [Team.objects.filter(is_fake=False,
        created_at__range=(d - diff, d)) for d in time_cohorts]

def growth(time_cohorts):
    return [u.count() for u in user_cohorts(time_cohorts)]

def team_growth(time_cohorts):
    return [t.count() for t in team_cohorts(time_cohorts)]

def daily_growth(n=30, days=1):
    dc = day_cohorts(n, days)
    return growth(dc)

def daily_team_growth(n=30, days=1):
    dc = day_cohorts(n, days)
    return team_growth(dc)

def weekly_growth(n=16):
    wc = week_cohorts(n)
    return growth(wc)

def weekly_team_growth(n=16):
    wc = week_cohorts(n)
    return team_growth(wc)

def active_users(queryset, period, new=True):
    if new:
        activations = UserActivation.objects.filter(timestamp__range=period, level__gte=UserActivation.LEVEL_PARTICIPATE)
        return queryset.filter(activations=activations).distinct()
    #In the future, when enough data is gathered, switch this by info in UserActivation
    fixtures = Fixture.objects.filter(start_date__range=period)
    matches = Match.objects.filter(fixture=fixtures, played__gt=0)
    return queryset.filter(matches=matches).distinct()

def lonely_users():
    tt = Team.objects.all().annotate(p=Count('players')).filter(p__lte=1)
    uu = get_user_model().objects.filter(is_staff=False, profile__isnull=False, profile__is_pro=False,
        membership=Membership.objects.filter(team=tt, state='state_active')).annotate(t=Count('teams')).filter(t__lte=1)
    uuu = get_user_model().objects.filter(is_staff=False, profile__isnull=False, profile__is_pro=False).annotate(t=Count('teams')).filter(t=0)
    return chain(uu,uuu)

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

def forecasts(fixture):
    Match.objects.filter(fixture=fixture).values('player').distinct().aggregate(p=Sum('played'))

def virality(b,k):
    if k >= 1:
        return "to the moon!"
    users = []
    prev = 0
    nxt = b
    prev_new_users = 0
    new_users = None
    while nxt > prev and (not new_users or prev_new_users > new_users):
        users += [nxt]
        prev_new_users = new_users or nxt
        new_users = round(k*(nxt - prev))
        prev = nxt
        nxt += new_users
    users += [nxt]
    return users[-1]

def cleanup_fake_teams():
    tt = Team.objects.filter(is_fake=True)
    Membership.objects.filter(team=tt).exclude(state='state_active').delete()

def activate_lonely_users(all_users=False):
    cleanup_fake_teams()
    tt = list(Team.objects.filter(is_fake=True).annotate(p=Count('players')).filter(p__lt=11))
    ti = iter(tt)
    t = next(ti)
    lu = lonely_users()
    for i,u in enumerate(lu):
        if all_users:
            t = random.choice(tt)
            t.sign(u)
        else:
            if t.players.count() == 11:
                try:
                    t = next(ti)
                except:
                    break
            t.sign(u)
