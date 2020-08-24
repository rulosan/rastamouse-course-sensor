#!venv/bin/python3

import os
import json
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv


class RastaCrawler (object):

    def __init__(self, url):
        self._url = url
        self.now = datetime.now()
        self.str_now = self.now.strftime("%Y-%m-%d %H:%M:%S")

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
                "stock": course["qtyInStock"]
            } for course in courses]
            in_stock = list(filter(lambda it: it['stock'] > 0, item_courses))
            return in_stock.pop() if len(in_stock) > 0 else None

    @property
    def current_date(self):
        return self.str_now


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
    cra = RastaCrawler(url)
    bot = TelegramBot(os.getenv("BOT_TOKEN"), os.getenv("ROGUE_CAMP_CHAT"))
    item = cra.has_stock()
    if item:
        msg = f"""
        Hay lugares para el Curso de Red Team del Rasta Mouse
        - {item.get("name")}
        - {item.get("price")}
        - {item.get("stock")}
        {url}
        """
        bot.send_message(msg)
    else:
        bot.send_message(
            "No hay ningun lugar en el curso de Rasta Mouse de Red Teamming :/")


if __name__ == '__main__':
    main()
