import requests
import time
from datetime import datetime, timedelta
import concurrent.futures

# Constants
API_BASE_URL = "https://api.exchange.coinbase.com"
MONITOR_INTERVAL = 300  # 5 minutes
VOLUME_THRESHOLD = 1000000  # $1 million in 24h volume
PRICE_CHANGE_THRESHOLD = 5  # 5% price change in 24h
MAX_CURRENCIES_TO_MONITOR = 20

class CryptoInvestmentScanner:
    def __init__(self):
        self.currencies = {}
        self.price_history = {}

    def fetch_usd_products(self):
        url = f"{API_BASE_URL}/products"
        response = requests.get(url)
        if response.status_code == 200:
            products = response.json()
            return [product['id'] for product in products if product['quote_currency'] == 'USD' and product['status'] == 'online']
        else:
            print(f"Error fetching products: {response.status_code}")
            return []

    def fetch_currency_stats(self, product_id):
        url = f"{API_BASE_URL}/products/{product_id}/stats"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
            stats = response.json()
            stats['id'] = product_id.split('-')[0]  # Extract the currency ID
            return stats
        except requests.exceptions.RequestException as e:
            return None

    def is_promising(self, stats):
        if not stats:
            return False
        try:
            volume = float(stats.get('volume', 0)) * float(stats.get('last', 0))
            last_price = float(stats.get('last', 0))
            open_price = float(stats.get('open', 0))
            
            if open_price == 0:
                return False  # Skip currencies with zero open price
            
            price_change = abs(last_price - open_price) / open_price * 100
            return volume > VOLUME_THRESHOLD and price_change > PRICE_CHANGE_THRESHOLD
        except (ValueError, TypeError):
            return False

    def update_promising_currencies(self):
        usd_products = self.fetch_usd_products()
        promising_currencies = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_product = {executor.submit(self.fetch_currency_stats, product_id): product_id for product_id in usd_products}
            for future in concurrent.futures.as_completed(future_to_product):
                stats = future.result()
                if stats and self.is_promising(stats):
                    promising_currencies.append((stats['id'], stats))

        promising_currencies.sort(key=lambda x: float(x[1]['volume']) * float(x[1]['last']), reverse=True)
        self.currencies = dict(promising_currencies[:MAX_CURRENCIES_TO_MONITOR])

    def calculate_metrics(self, stats):
        try:
            last_price = float(stats['last'])
            open_price = float(stats['open'])
            volume = float(stats['volume']) * last_price
            
            if open_price == 0:
                return None  # Skip currencies with zero open price
            
            price_change = (last_price - open_price) / open_price * 100
            return {
                'price': last_price,
                'volume': volume,
                'price_change': price_change
            }
        except (ValueError, TypeError, KeyError):
            return None

    def run(self):
        print("Cryptocurrency Investment Scanner Started")
        print(f"Scanning for promising cryptocurrencies...")
        print(f"Criteria: 24h volume > ${VOLUME_THRESHOLD:,} and 24h price change > {PRICE_CHANGE_THRESHOLD}%")
        print("Press Ctrl+C to stop the program")
        
        while True:
            self.update_promising_currencies()
            print(f"\nTop {len(self.currencies)} promising cryptocurrencies:")
            for currency_id, stats in self.currencies.items():
                metrics = self.calculate_metrics(stats)
                if metrics:
                    print(f"{currency_id}:")
                    print(f"  Price: ${metrics['price']:.2f}")
                    print(f"  24h Volume: ${metrics['volume']:,.2f}")
                    print(f"  24h Price Change: {metrics['price_change']:.2f}%")
            print("-" * 40)
            time.sleep(MONITOR_INTERVAL)

if __name__ == "__main__":
    scanner = CryptoInvestmentScanner()
    scanner.run()