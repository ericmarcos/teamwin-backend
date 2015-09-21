from django.contrib import admin
from django.utils.html import format_html
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

    def button(self, obj):
        if not obj.is_set():
            html =  ('<button type="button" onclick="set_pool({0}, \'1\');">1</button>'
                     '<button type="button" onclick="set_pool({0}, \'X\');">X</button>'
                     '<button type="button" onclick="set_pool({0}, \'2\');">2</button>')
            html = html.format(obj.id)
        else:
            w = obj.winner_result()
            html = 'Winner result: <strong>{0}</strong>'.format(w.name if w else None)
        return format_html(html)
    button.short_description = 'Winner result'
    button.allow_tags = True

    def fixture(self, obj):
        return obj.fixtures.first()

    def league(self, obj):
        try:
            return obj.fixtures.first().league.name
        except:
            return None

    list_display = ('id', '__unicode__', 'fixture', 'closing_date', 'league', 'state', 'button')
    list_filter = ('state', 'fixtures__league', 'fixtures')
    ordering = ('-closing_date',)

    class Media:
        js = (
            'admin/js/set_pool.js',   # app static folder
        )


class MembershipInline(admin.StackedInline):
    model = Membership
    extra = 0


class TeamAdmin(admin.ModelAdmin):
    inlines = [MembershipInline, ]
    search_fields = ('name',)


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
