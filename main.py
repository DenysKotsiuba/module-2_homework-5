import aiohttp
import asyncio

from abc import ABC, abstractmethod

import platform
import sys

from collections import UserDict, UserList

from datetime import date, timedelta
from time import time


class Currency(ABC):
    @abstractmethod
    def get_sale_rate(self):
        pass


class DollarCurrency(Currency):
    def __init__(self, sale=None, purchase=None, name="USD"):
        self.name = name
        self.sale = sale
        self.purchase = purchase

    def get_sale_rate(self, data):
        currencies = data["exchangeRate"]
        for currency in currencies:
            match currency["currency"]:
                case self.name:
                    self.sale = currency["saleRate"]
                    self.purchase = currency["purchaseRate"]


class EuroCurrency(Currency):
    def __init__(self, sale=None, purchase=None, name="EUR"):
        self.name = name
        self.sale = sale
        self.purchase = purchase

    def get_sale_rate(self, data):
        currencies = data["exchangeRate"]
        for currency in currencies:
            match currency["currency"]:
                case self.name:
                    self.sale = currency["saleRate"]
                    self.purchase = currency["purchaseRate"]


class CurrenciesExchange(UserDict):
    def __init__(self, *currencies, date=None):
        self.date = date
        self.currencies = currencies
    
    def get_record(self, private_bank_data):
        data = {}
        self.date = private_bank_data["date"]
        data[self.date] = {}

        for currency in self.currencies:
            currency.get_sale_rate(private_bank_data)
            exchange_rate = {}
            exchange_rate[currency.name] = {"sale": currency.sale, "purchase": currency.purchase}
            data[self.date].update(exchange_rate)
        return data
    
    
def get_date(number):
    now = date.today()
    my_date_object = now - timedelta(days=number)
    my_date = my_date_object.strftime("%d.%m.%Y")
    return my_date


async def get_response(date, session):
    url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
    try:
        async with session.get(url) as response:
            if response.ok:
                return await response.json()
            else:
                print(f"Error status {response.status} for {url}.")
    except aiohttp.ClientConnectionError as error:
        print("Connection error: {url}", str(error))


async def main():
    days_number = int(sys.argv[1])
    if days_number > 10:
        print("maximum number of days: 10")
        days_number = 10
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[get_response(get_date(day), session) for day in range(days_number)])


if __name__ == "__main__":
    start = time()

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        private_bank_data = asyncio.run(main())

    euro = EuroCurrency()
    dollar = DollarCurrency()
    currencies_exchange = CurrenciesExchange(euro, dollar)
    processed_data = list(map(currencies_exchange.get_record, private_bank_data))
    print(processed_data)

    print(time()-start)