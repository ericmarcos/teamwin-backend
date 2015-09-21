import requests as r
from bs4 import BeautifulSoup
from ftfy import fix_text
from .models import *


def get_bwin_odds():
    pools = Pool.objects.filter(fixtures__league__name='Champions Bwin').open()
    def is_champions(item):
        return item.name == 'league' and item.has_attr('name') and 'Liga de Campeones' in item['name']
    def is_game_1X2(item):
        return item.name == 'games' and item.has_attr('name') and item['name'] == '1 X 2'
    x = r.get('https://mediaserver.bwinpartypartners.com/renderBanner.do?zoneId=1671194')
    soup = BeautifulSoup(x.text.encode('utf-8'), "xml")
    leagues = soup.findAll(is_champions)
    for l in leagues:
        games = l.findAll(is_game_1X2)
        for g in games:
            option1 = ""
            option2 = ""
            home, tie, away = [{
                'name': fix_text(res['name']),
                'odd': float(res['odd'])}
                for res in g.findAll('result')]

            p = pools.filter(options__item__bwin_name=home['name']).filter(
                options__item__bwin_name=away['name']).first()
            if p:
                print 'Updating %s' % p
                PoolResult.objects.update_or_create(pool=p, name='1', defaults={'bwin_odds': home['odd']})
                PoolResult.objects.update_or_create(pool=p, name='X', defaults={'bwin_odds': tie['odd']})
                PoolResult.objects.update_or_create(pool=p, name='2', defaults={'bwin_odds': away['odd']})

