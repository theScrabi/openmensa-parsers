from urllib.request import urlopen
from bs4 import BeautifulSoup as parse
import re

from utils import Parser

from pyopenmensa.feed import LazyBuilder, extractDate

price_regex = re.compile(r'(?P<price>\d+[,.]\d{2}) ?€')
speiseplan_regex = re.compile(r'^Speiseplan\s+')
kein_angebot_regex = re.compile(r'kein Angebot')

roles = ('student', 'employee')


def parse_week(url, canteen):
    data = urlopen(url).read().decode('utf-8')
    document = parse(data, 'lxml')

    # The day plans are in a div with no special class or id. Thus
    # we try to find a div with a heading "Speiseplan "
    for week_heading in document(class_='swdd-ueberschrift',
                                 text=speiseplan_regex):
        week_div = week_heading.parent

        # The meals for each day a in card. Again there is no class or id to
        # select the meal cards. Thus we lookung for all card with a card-header
        # which stores the date
        for card_header in week_div.find_all(class_='card-header'):
            day_card = card_header.parent

            try:
                date = extractDate(card_header.text)
            except ValueError:
                # There was no valid date in the table header, which happens eg
                # for special "Aktionswoche" cards.
                # TODO: check if this card contains any meals, which was not the
                #       case when it was used for the first time.
                continue

            # Check if there is a "kein Angebot" item
            if day_card.find(class_='list-group-item', text=kein_angebot_regex):
                canteen.setDayClosed(date)
                continue

            # Iterate over the list-group-item within the card which are used
            # for individual meals
            for meal in day_card.find_all(class_='swdd-link-list-item'):

                name = meal.find(name='span')
                if name is not None:
                    name = name.text
                else:
                    continue

                if ': ' in name:
                    category, name = name.split(': ', 1)
                else:
                    category = 'Angebote'

                notes = [img['alt'] for img in meal.find_all(class_='swdd-spl-symbol')]

                if '* ' in name:
                    name, note = name.split('* ', 1)
                    notes.append(note)

                if meal.strong is not None:
                    prices = price_regex.findall(meal.strong.text)
                else:
                    prices = []

                canteen.addMeal(date, category, name, notes,
                                prices, roles)


def parse_url(url, today=False):
    canteen = LazyBuilder()
    parse_week(url + '.html?view=list', canteen)
    if not today:
        parse_week(url + '-w1.html?view=list', canteen)
        parse_week(url + '-w2.html?view=list', canteen)
    return canteen.toXMLFeed()


parser = Parser('dresden', handler=parse_url,
                shared_prefix='https://www.studentenwerk-dresden.de/mensen/speiseplan/')
parser.define('dresden-reichenbachstrasse', suffix='mensa-reichenbachstrasse')
parser.define('dresden-zeltschloesschen', suffix='zeltschloesschen')
parser.define('dresden-alte-mensa', suffix='alte-mensa')
parser.define('dresden-mensologie', suffix='mensologie')
parser.define('dresden-siedepunkt', suffix='mensa-siedepunkt')
parser.define('dresden-johannstadt', suffix='mensa-johannstadt')
parser.define('tharandt-tellerrandt', suffix='mensa-tellerrandt')
parser.define('dresden-palucca-hochschule', suffix='mensa-palucca-hochschule')
parser.define('dresden-wueins', suffix='mensa-wueins')
parser.define('dresden-bruehl', suffix='mensa-bruehl')
parser.define('dresden-stimm-gabel', suffix='mensa-stimm-gabel')
parser.define('dresden-u-boot', suffix='u-boot')
parser.define('dresden-mensa-sport', suffix='mensa-sport')
parser.define('dresden-cafe-cube', suffix='grill-cube')
parser.define('dresden-cafe-mobil', suffix='pasta-mobil')
parser.define('zittau-kraatschn', suffix='mensa-kraatschn')
parser.define('zittau-mahlwerk', suffix='mensa-mahlwerk')
parser.define('goerlitz-mio', suffix='mio-mensa-im-osten')
parser.define('rothenburg-mensa', suffix='mensa-rothenburg')
parser.define('bautzen-polizeihochschule', suffix='mensa-bautzen')
parser.define('bautzen-oberschmausitz', suffix='mensa-oberschmausitz')
