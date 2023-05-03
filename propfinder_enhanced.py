import requests
from bs4 import BeautifulSoup
from hashlib import sha1
from urllib.parse import urlparse
from dataclasses import dataclass
import cloudscraper
from time import sleep
from random import randint
import json


genericQueries = {
 "https://www.zonaprop.com.ar/departamentos-ph-venta-palermo-belgrano-colegiales-nunez-mas-de-2-banos-mas-de-3-habitaciones-mas-de-1-garage-30000-230000-dolar-orden-publicado-descendente",
 "https://www.zonaprop.com.ar/departamentos-ph-venta-palermo-belgrano-colegiales-nunez-mas-de-2-banos-mas-de-2-habitaciones-mas-de-1-garage-30000-200000-dolar-orden-publicado-descendente",
 }


def get_telegram_keys():
    with open('telegram_bot_keys.json') as f:
        data = json.load(f)
        botID, roomID = data.values()
        return botID, roomID


@dataclass
class Parser:
    website: str
    link_regex: str

    def extract_links(self, contents: str):
        soup = BeautifulSoup(contents, "lxml")
        ads = soup.select(self.link_regex)
        for ad in ads:
            href = ad["href"]
            _id = sha1(href.encode("utf-8")).hexdigest()
            yield {"id": _id, "url": "{}{}".format(self.website, href)}


parsers = [
    # Parser(website="https://www.zonaprop.com.ar", link_regex="h2.sc-i1odl-10 a.sc-i1odl-11.hDkIKM"),
    Parser(website="https://www.zonaprop.com.ar", link_regex="h2.sc-i1odl-10 a.sc-i1odl-11.kptTyQ"),
    Parser(website="https://www.argenprop.com", link_regex="div.listing__items div.listing__item a"),
    Parser(website="https://inmuebles.mercadolibre.com.ar", link_regex="li.results-item .rowItem.item a"),
]


def extract_ads(url, text):
    uri = urlparse(url)
    parser = next(p for p in parsers if uri.hostname in p.website)
    return parser.extract_links(text)


def split_seen_and_unseen(ads):
    history = get_history()
    seen = [a for a in ads if a["id"] in history]
    unseen = [a for a in ads if a["id"] not in history]
    return seen, unseen


def sleep_func(min=1, max=5):
    delay = randint(min, max)
    print("Sleep " + str(delay) + "s")
    sleep(delay)


def get_history():
    try:
        with open("seen.txt", "r") as f:
            return {l.rstrip() for l in f.readlines()}
    except:
        return set()


def telegram_notify(ad):
    botID, roomID = get_telegram_keys()
    url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(botID, roomID, ad["url"])
    r = requests.get(url)


def mark_as_seen(unseen):
    with open("seen.txt", "a+") as f:
        ids = ["{}\n".format(u["id"]) for u in unseen]
        f.writelines(ids)


def url_composer(url, page=0):
    if page != 0:
        url = url + "-pagina-" + str(page)
    return url + ".html"


def _main():
    scraper = cloudscraper.create_scraper(browser={
        'custom': 'ScraperBot/1.0'
    }, delay=10)
    for query in genericQueries:

        page = 0

        while True:
            url = url_composer(query, page=page)
            print("Extracting from: ", url)
            try:
                res = scraper.get(url)
            except:
                sleep_func()
                res = scraper.get(url)

            ads = list(extract_ads(url, res.text))
            if not len(ads):
                print("Not able to extract ads, check regex.")
            seen, unseen = split_seen_and_unseen(ads)

            print("{} seen, {} unseen".format(len(seen), len(unseen)))

            for u in unseen:
                telegram_notify(u)

            mark_as_seen(unseen)

            print("Done")
            #if len(seen):
            if page != 20:
                page += 1
                sleep_func()
            else:
                break


if __name__ == "__main__":
    _main()
