import requests as r
from bs4 import BeautifulSoup
from ftfy import fix_text
from .models import *


def get_bwin_oods():
    teams = ['Lyon', 'Valencia'] #TODO: get all teams names
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
            for result in g.findAll('result'):
                print fix_text(result['name']), result['odd']
            print '----------------------------'
