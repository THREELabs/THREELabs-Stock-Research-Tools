import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

class CoinbaseAnalyzer:
    def __init__(self):
        # Updated to use the new Coinbase API endpoint
        self.base_url = "https://api.exchange.coinbase.com"
        
    def get_products(self):
        """Get list of available trading pairs"""
        try:
            response = requests.get(f"{self.base_url}/products")
            print(f"API Status Code: {response.status_code}")  # Debug print
            
            if response.status_code == 200:
                products = response.json()
                print(f"Found {len(products)} total products")  # Debug print
                return products
            else:
                print(f"Error response: {response.text}")  # Debug print
                return []
        except Exception as e:
            print(f"Error fetching products: {str(e)}")
            return []
        
    def get_product_stats(self, product_id):
        """Get 24hr stats for a specific trading pair"""
        try:
            response = requests.get(f"{self.base_url}/products/{product_id}/stats")
            if response.status_code == 200:
                return response.json()
            print(f"Error getting stats for {product_id}: {response.text}")
            return None
        except Exception as e:
            print(f"Error getting stats for {product_id}: {str(e)}")
            return None
    
    def get_historical_data(self, product_id, start, end, granularity=3600):
        """Get historical price data"""
        try:
            params = {
                'start': start.isoformat(),
                'end': end.isoformat(),
                'granularity': granularity
            }
            response = requests.get(f"{self.base_url}/products/{product_id}/candles", params=params)
            
            if response.status_code != 200:
                print(f"Error getting historical data for {product_id}: {response.text}")
                return None
                
            data = response.json()
            
            if not isinstance(data, list) or len(data) < 20:
                print(f"Insufficient historical data for {product_id}")
                return None
                
            return data
            
        except Exception as e:
            print(f"Error getting historical data for {product_id}: {str(e)}")
            return None
    
    def calculate_metrics(self, data):
        """Calculate technical indicators"""
        try:
            # Convert to DataFrame and handle reverse chronological order
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.sort_values('time')
            
            # Calculate RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Calculate volume trend
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_trend'] = df['volume'] / df['volume_sma']
            
            # Calculate volatility
            df['volatility'] = df['close'].pct_change().rolling(window=20).std()
            
            return df
            
        except Exception as e:
            print(f"Error calculating metrics: {str(e)}")
            return None
    
    def scan_for_opportunities(self, min_volume=10000):
        """Scan for potential opportunities based on technical indicators"""
        opportunities = []
        
        # Get all available trading pairs
        products = self.get_products()
        if not products:
            print("No products found to analyze")
            return opportunities
        
        print(f"\nAnalyzing {len(products)} products...")
        
        for product in products:
            try:
                product_id = product.get('id')
                if not product_id:
                    continue
                
                # Only analyze USD trading pairs with sufficient volume
                if not product_id.endswith('-USD'):
                    continue
                
                print(f"\nAnalyzing {product_id}...")
                
                # Get recent stats
                stats = self.get_product_stats(product_id)
                if not stats:
                    continue
                    
                volume = float(stats.get('volume', 0))
                if volume < min_volume:
                    print(f"Skipping {product_id} - insufficient volume: ${volume:,.2f}")
                    continue
                
                print(f"24h Volume: ${volume:,.2f}")
                
                # Get historical data
                end = datetime.now()
                start = end - timedelta(days=7)
                historical_data = self.get_historical_data(product_id, start, end)
                
                if not historical_data:
                    continue
                
                # Calculate metrics
                df = self.calculate_metrics(historical_data)
                if df is None or df.empty:
                    continue
                
                latest = df.iloc[-1]
                
                # Check for significant indicators
                conditions = {}
                
                if pd.notnull(latest['RSI']):
                    conditions['oversold'] = latest['RSI'] < 30
                    print(f"RSI: {latest['RSI']:.2f}")
                
                if pd.notnull(latest['volume_trend']):
                    conditions['high_volume'] = latest['volume_trend'] > 2.0
                    print(f"Volume Trend: {latest['volume_trend']:.2f}x average")
                
                if pd.notnull(latest['volatility']):
                    conditions['increasing_volatility'] = latest['volatility'] > df['volatility'].mean()
                    print(f"Volatility: {latest['volatility']:.2f}")
                
                if any(conditions.values()):
                    print(f"Found opportunity in {product_id}!")
                    opportunities.append({
                        'product_id': product_id,
                        'price': latest['close'],
                        'volume': volume,
                        'indicators': conditions
                    })
                
                # Respect API rate limits
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error analyzing {product_id if 'product_id' in locals() else 'unknown'}: {str(e)}")
                continue
        
        return opportunities

def main():
    analyzer = CoinbaseAnalyzer()
    print("Starting market analysis...")
    opportunities = analyzer.scan_for_opportunities(min_volume=100000)  # Lowered minimum volume threshold
    
    if not opportunities:
        print("\nNo opportunities found matching the criteria.")
        return
        
    print(f"\nFound {len(opportunities)} potential opportunities:")
    for opp in opportunities:
        print(f"\nProduct: {opp['product_id']}")
        print(f"Current Price: ${opp['price']:,.2f}")
        print(f"24h Volume: ${opp['volume']:,.2f}")
        print("Indicators:")
        for indicator, value in opp['indicators'].items():
            if value:
                print(f"- {indicator}")
        print("-" * 50)

if __name__ == "__main__":
    main()