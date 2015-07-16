from django.contrib import admin
from .models import *


class PoolResultInline(admin.StackedInline):
    model = PoolResult
    extra = 0
    readonly_fields = ('is_winner',)


class PoolOptionInline(admin.StackedInline):
    model = PoolOption
    extra = 0


class PoolAdmin(admin.ModelAdmin):
    inlines = [PoolResultInline, PoolOptionInline, ]


class MembershipInline(admin.StackedInline):
    model = Membership
    extra = 0


class TeamAdmin(admin.ModelAdmin):
    inlines = [MembershipInline, ]


admin.site.register(Pool, PoolAdmin)
admin.site.register(Item)
admin.site.register(Team, TeamAdmin)


class PrizeInline(admin.StackedInline):
    model = Prize
    extra = 0


class FixtureInline(admin.StackedInline):
    model = Fixture
    extra = 0


class LeagueAdmin(admin.ModelAdmin):
    inlines = [PrizeInline, FixtureInline, ]


admin.site.register(League, LeagueAdmin)
