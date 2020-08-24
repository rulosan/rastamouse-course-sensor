#!venv/bin/python3

import os
import json
import requests
import logging

from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv


def setup_logging(name: str, filename: str,
                  format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(filename)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter(format)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


class RastaCrawler (object):

    def __init__(self, url: str, logger: logging.Logger):
        self._url = url
        self.logger = logger

    def has_stock(self):
        session = requests.session()
        try:
            resp = session.get(self._url)
        except Exception as ex:
            print(str(ex))
        else:
            soup = BeautifulSoup(resp.text, "html5lib")
            info = soup("div", {"class": "product-variants"})[0]
            dv = info.attrs['data-variants']
            courses = json.loads(dv)
            item_courses = [{
                "name": course["attributes"]["Package"],
                "price": f"{course['priceMoney']['currency']} {course['priceMoney']['value']}",
                "stock": int(course["qtyInStock"])
            } for course in courses]
            in_stock = list(filter(lambda it: it['stock'] > 0, item_courses))
            self.logger.info(f"{len(in_stock)} elementos en el stock")
            session.close()
            return in_stock.pop() if len(in_stock) > 0 else None


class TelegramBot (object):

    def __init__(self, bot_token:str, chat_id: str):
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._qstring = {
            "chat_id": chat_id,
            "parse_mode": "Markdown",
        }

    def send_message(self, message: str):
        self._qstring["text"] = message
        try:
            res = requests.get(self._url, params=self._qstring)
        except Exception as ex:
            print(str(ex))
        else:
            if res.status_code == 200:
                print("Se envio correctamente")


def main():
    load_dotenv()
    url = os.getenv("ZEROPOINT_URL")
    logger = setup_logging(os.getenv("LOGNAME"), os.getenv("LOGFILE"))
    cra = RastaCrawler(url, logger)
    bot = TelegramBot(os.getenv("BOT_TOKEN"), os.getenv("ROGUE_CAMP_CHAT"))
    stock_item = cra.has_stock()
    if stock_item:
        logger.info("Hay lugares disponibles :D ... comprar...")
        msg = f"""
        Hay lugares para el Curso de Red Team del Rasta Mouse
        - {stock_item.get("name")}
        - {stock_item.get("price")}
        - {stock_item.get("stock")}
        {url}
        """
        bot.send_message(msg)
    else:
        logger.info(f"No hay lugares disponibles ... siga intentando")


if __name__ == '__main__':
    main()
