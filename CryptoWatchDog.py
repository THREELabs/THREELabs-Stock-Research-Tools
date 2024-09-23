import requests
import time
from datetime import datetime, timedelta

# Constants
API_BASE_URL = "https://api.exchange.coinbase.com"
MONITOR_INTERVAL = 60  # seconds
TARGET_DROP_PERCENTAGE = 15  # 15% drop to trigger a buy signal
PROFIT_TAKE_PERCENTAGE = 7  # 7% profit to trigger a sell signal
CURRENCIES_TO_MONITOR = ["BTC", "ETH", "ADA", "DOT", "XRP"]  # Example currencies

class CryptoTradingAssistant:
    def __init__(self):
        self.currencies = {}
        self.price_history = {}

    def fetch_currency_price(self, currency):
        url = f"{API_BASE_URL}/products/{currency}-USD/ticker"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return float(data['price'])
        else:
            print(f"Error fetching price for {currency}: {response.status_code}")
            return None

    def update_prices(self):
        for currency in CURRENCIES_TO_MONITOR:
            price = self.fetch_currency_price(currency)
            if price is not None:
                self.currencies[currency] = price

    def calculate_price_change(self, currency):
        if currency not in self.price_history:
            self.price_history[currency] = []
        
        self.price_history[currency].append((datetime.now(), self.currencies[currency]))
        
        # Remove price data older than 24 hours
        self.price_history[currency] = [
            (t, p) for t, p in self.price_history[currency] 
            if t > datetime.now() - timedelta(hours=24)
        ]
        
        if len(self.price_history[currency]) < 2:
            return 0
        
        oldest_price = self.price_history[currency][0][1]
        current_price = self.price_history[currency][-1][1]
        return ((current_price - oldest_price) / oldest_price) * 100

    def check_buy_signal(self, currency):
        price_change = self.calculate_price_change(currency)
        if price_change <= -TARGET_DROP_PERCENTAGE:
            print(f"BUY SIGNAL: {currency} has dropped by {abs(price_change):.2f}%")
            return True
        return False

    def check_sell_signal(self, currency):
        price_change = self.calculate_price_change(currency)
        if price_change >= PROFIT_TAKE_PERCENTAGE:
            print(f"SELL SIGNAL: {currency} has increased by {price_change:.2f}%")
            return True
        return False

    def run(self):
        print("Cryptocurrency Trading Assistant Started")
        print(f"Monitoring: {', '.join(CURRENCIES_TO_MONITOR)}")
        print(f"Buy Signal: {TARGET_DROP_PERCENTAGE}% drop")
        print(f"Sell Signal: {PROFIT_TAKE_PERCENTAGE}% profit")
        print("Press Ctrl+C to stop the program")
        
        while True:
            self.update_prices()
            for currency in CURRENCIES_TO_MONITOR:
                if currency in self.currencies:
                    print(f"{currency}: ${self.currencies[currency]:.2f}")
                    self.check_buy_signal(currency)
                    self.check_sell_signal(currency)
            print("-" * 40)
            time.sleep(MONITOR_INTERVAL)

if __name__ == "__main__":
    assistant = CryptoTradingAssistant()
    assistant.run()