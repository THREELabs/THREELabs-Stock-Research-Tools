import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CryptoVolatilityTracker:
    def __init__(self, exchange='coinbase', timeframe='1h', window=24, volatility_threshold=1.5):
        self.exchange = getattr(ccxt, exchange)()
        self.timeframe = timeframe
        self.window = window
        self.volatility_threshold = volatility_threshold
        self.data = {}

    def fetch_data(self):
        try:
            markets = self.exchange.load_markets()
            for symbol in markets:
                if markets[symbol]['active']:
                    ohlcv = self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=self.window)
                    if len(ohlcv) == self.window:
                        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                        df.set_index('timestamp', inplace=True)
                        self.data[symbol] = df
            logging.info(f"Fetched data for {len(self.data)} symbols")
        except Exception as e:
            logging.error(f"Error fetching data: {str(e)}")

    def calculate_volatility(self):
        for symbol, df in self.data.items():
            returns = df['close'].pct_change()
            volatility = returns.std() * np.sqrt(self.window)
            self.data[symbol]['volatility'] = volatility

    def identify_opportunities(self):
        avg_volatility = np.mean([df['volatility'].iloc[-1] for df in self.data.values()])
        opportunities = []

        for symbol, df in self.data.items():
            volatility = df['volatility'].iloc[-1]
            if volatility > avg_volatility * self.volatility_threshold:
                volume = df['volume'].iloc[-1]
                price = df['close'].iloc[-1]
                trend = 'up' if df['close'].iloc[-1] > df['close'].iloc[0] else 'down'
                score = self.calculate_score(volatility, volume, trend)
                opportunities.append({
                    'symbol': symbol,
                    'volatility': volatility,
                    'volume': volume,
                    'price': price,
                    'trend': trend,
                    'score': score
                })

        return sorted(opportunities, key=lambda x: x['score'], reverse=True)

    def calculate_score(self, volatility, volume, trend):
        # This is a simple scoring system. You may want to refine this based on your strategy.
        vol_score = volatility * 2  # Higher volatility is good
        vol_score = volume / 1000000  # Normalize volume, assuming in millions
        trend_score = 1 if trend == 'up' else 0.5  # Prefer upward trends
        return (vol_score + vol_score + trend_score) / 3

    def generate_report(self, opportunities):
        print("Crypto Volatility Tracker Report")
        print("================================")
        print(f"Average Volatility: {np.mean([df['volatility'].iloc[-1] for df in self.data.values()]):.4f}")
        print(f"Number of opportunities: {len(opportunities)}")
        print("\nTop 10 Opportunities:")
        for i, opp in enumerate(opportunities[:10], 1):
            print(f"{i}. {opp['symbol']}:")
            print(f"   Volatility: {opp['volatility']:.4f}")
            print(f"   Volume: {opp['volume']:.2f}")
            print(f"   Price: {opp['price']:.2f}")
            print(f"   Trend: {opp['trend']}")
            print(f"   Score: {opp['score']:.2f}")
            print(f"   Suggested max investment: ${min(opp['volume']*0.01, 1000):.2f}")
            print(f"   Suggested stop-loss: ${opp['price']*0.95:.2f}")
            print()

    def run(self):
        while True:
            self.fetch_data()
            self.calculate_volatility()
            opportunities = self.identify_opportunities()
            self.generate_report(opportunities)
            time.sleep(3600)  # Run every hour

if __name__ == "__main__":
    tracker = CryptoVolatilityTracker()
    tracker.run()
