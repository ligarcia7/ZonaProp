from __future__ import annotations
import requests
from bs4 import BeautifulSoup
from hashlib import sha1
from urllib.parse import urlparse
from dataclasses import dataclass
import cloudscraper
from time import sleep
from random import randint
import json
from typing import Generator
import logging

logging.basicConfig(
         format='%(asctime)s %(levelname)-8s %(message)s',
         level=logging.DEBUG,
         datefmt='%Y-%m-%d %H:%M:%S'
)

genericQueries = {
 "https://www.zonaprop.com.ar/departamentos-ph-venta-palermo-belgrano-colegiales-nunez-mas-de-2-banos-mas-de-3-habitaciones-mas-de-1-garage-30000-230000-dolar-orden-publicado-descendente.html",
 "https://www.zonaprop.com.ar/departamentos-ph-venta-palermo-belgrano-colegiales-nunez-mas-de-2-banos-mas-de-3-habitaciones-mas-de-1-garage-231000-245000-dolar-orden-publicado-descendente.html",
 "https://www.zonaprop.com.ar/departamentos-ph-venta-palermo-belgrano-colegiales-nunez-mas-de-2-banos-mas-de-2-habitaciones-mas-de-1-garage-30000-200000-dolar-orden-publicado-descendente.html",
}


def get_telegram_keys(file_path: str = 'telegram_bot_keys.json') -> tuple[str, str]:
    """
    Load Telegram bot and chat room IDs from a JSON file.

    Args:
        file_path (str): Optional. The path and filename of the JSON file containing the bot and chat room IDs.
            Default is 'telegram_bot_keys.json' in the current working directory.

    Returns:
        tuple: A tuple containing two strings - the bot ID and room ID - loaded from the JSON file.

    Raises:
        FileNotFoundError: If the 'telegram_bot_keys.json' file cannot be found in the specified directory.
        json.JSONDecodeError: If the JSON data in the file is invalid.
        KeyError: If the JSON data does not contain 'bot_http_token' or 'roomID' keys.
    """
    try:
        with open(file_path) as f:
            data = json.load(f)
            bot_http_token, roomID = data.values()
            return bot_http_token, roomID
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{file_path}' not found.")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"Invalid JSON data in file '{file_path}'.")
    except KeyError as e:
        raise KeyError(f"JSON data in file '{file_path}' is missing key '{e.args[0]}'.")


@dataclass
class Parser:
    """
    A class that parses a website's HTML content and extracts links matching a specific regular expression.
    Making this class a dataclass is reasonable because it primarily stores data (website and link regex)

    Attributes:
    website (str): The website from which the links will be extracted.
    link_regex (str): The regular expression pattern used to match the links.

    Methods:
    extract_links(contents: str) -> generator:
    Extracts links from the provided HTML content that match the link_regex pattern, and yields a dictionary
    for each link containing an id and the full url constructed by concatenating the website and the link.
    """
    website: str
    link_regex: str

    def extract_links(self, contents: str) -> dict[str, str]:
        soup = BeautifulSoup(contents, "lxml")
        ads = soup.select(self.link_regex)
        if not ads:
            logging.warning(f"Not able to extract ads in {self.website}, check regex: {self.link_regex}")
            yield {}
        for ad in ads:
            href = ad["href"]
            _id = sha1(href.encode("utf-8")).hexdigest()
            yield {"id": _id, "url": "{}{}".format(self.website, href)}


class Extractor:

    def __init__(self) -> None:
        self.parsers = self.load_parsers()

    @staticmethod
    def load_parsers(file_path: str = 'sites.json') -> list[Parser]:
        parsers = []
        try:
            with open(file_path) as f:
                data = json.load(f)
                for site, link_regex in data.items():
                    parsers.append(Parser(website=site, link_regex=link_regex))
        except FileNotFoundError:
            raise FileNotFoundError(f"File '{file_path}' not found.")
        except json.JSONDecodeError:
            raise json.JSONDecodeError(f"Invalid JSON data in file '{file_path}'.")
        except KeyError as e:
            raise KeyError(f"JSON data in file '{file_path}' is missing key '{e.args[0]}'.")
        return parsers

    def extract_ads(self, url: str, text: str) -> Generator:  # TODO: make type hinting more specific for Generator
        """
        Extracts ads from the provided HTML content that match a specified regular expression pattern.

        Args:
        url (str): The URL of the website from which to extract ads.
        text (str): The HTML content to search for ads.
        Returns:
        generator: A generator that yields a dictionary for each ad containing an id and the full url of the ad.
        """
        uri = urlparse(url)
        parser = next(p for p in self.parsers if uri.hostname in p.website)
        return parser.extract_links(text)


def split_seen_and_unseen(ads: dict) -> tuple[list, list]:  # TODO: Make dict type hinting more specific
    """
    Splits a list of ads into two lists - seen and unseen.

    Args:
    ads (list): A list of ads, each represented by a dictionary containing an id and the full url of the ad.

    Returns:
    tuple: A tuple containing two lists - seen and unseen - where seen is a list of ads that have already been seen, and unseen is a list of ads that have not been seen.
    """
    history = get_history(filename='seen.txt')
    seen = [a for a in ads if a["id"] in history]
    unseen = [a for a in ads if a["id"] not in history]
    return seen, unseen


def sleep_func(_min: int = 1, _max: int = 5) -> None:
    """
    Delays program execution for a random amount of time between min and max seconds.
    """
    delay = randint(_min, _max)
    logging.info(f"Sleeping for {delay} s")
    sleep(delay)


def create_file(filename: str) -> 'None':
    """
    Creates file and return an empty dictionary
    """
    with open(filename, "w") as f:
        logging.info(f'{filename} has been created.')


def get_history(filename: str) -> set(str):
    """
    Attempts to load a set of previously seen ads from a text file called "seen.txt" in the current working directory. If the file does not exist or cannot be loaded, an empty set is returned.
    Returns:
    set: A set of previously seen ad IDs.
    """
    try:
        with open(filename) as f:
            return {l.rstrip() for l in f.readlines()}
    except FileNotFoundError:
        logging.info(f'{filename} not found.')
        try:
            create_file(filename)
            return {}
        except OSError as e:
            logging.error(f"Couldn't create {filename} due to {e}")
            return {}


def telegram_notify(msg:str) -> None:  # TODO: Make dict type hinting more specific
    """
    Sends a notification to a Telegram chat room containing the full URL of a new ad.
    """
    botID, roomID = get_telegram_keys()
    url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(botID, roomID, msg)
    _ = requests.get(url)


def mark_as_seen(unseen: list) -> None: # TODO: Make list type hinting more specific
    """
    Adds a set of unseen ads to a text file called "seen.txt" in the current working directory, marking them as seen.
    """
    with open("seen.txt", "a+") as f:
        ids = ["{}\n".format(u["id"]) for u in unseen]
        f.writelines(ids)


def url_paginator(url: str, page: int = 0) -> str:
    """
    Composes a URL string with an optional page number.
    """
    return f'{url[:-len(".html")]}-pagina-{page}.html' if page else url


def _main() -> None:
    ad_count = 0
    scraper = cloudscraper.create_scraper(browser={
        'custom': 'ScraperBot/1.0'
    }, delay=10)
    for query in genericQueries:

        page = 0

        while True:
            url = url_paginator(query, page=page)
            logging.debug(f"Extracting from: {url}")
            res = scraper.get(url)
            extractor = Extractor()
            ads = list(extractor.extract_ads(url, res.text))

            seen, unseen = split_seen_and_unseen(ads)
            logging.info(f"{len(seen)} seen ads, {len(unseen)} unseen ads")

            for u in unseen:
                telegram_notify(u["url"])


            mark_as_seen(unseen)

            if unseen:
                page += 1
                ad_count += len(unseen)
                sleep_func()
            else:
                logging.info('No unseen ads. Moving on.')
                break
    finalMsj = f'Process completed. Found {ad_count} unseen ads.'
    telegram_notify(finalMsj)
    logging.info(finalMsj)


if __name__ == "__main__":
    _main()
