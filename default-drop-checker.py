import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests

# Configurable Parameters
ANALYSIS_TYPE = 'both'  # Choose to analyze 'crypto', 'stocks', or 'both'
MIN_FLUCTUATION = 2  # Minimum percentage fluctuation to consider
MAX_FLUCTUATION = 10  # Maximum percentage fluctuation to consider
CONSECUTIVE_WEEKS = 3  # Number of consecutive weeks to check for fluctuation pattern
LOOKBACK_WEEKS = 12  # Number of weeks to look back for analysis
MAX_INSTRUMENTS_TO_ANALYZE = 2000  # Maximum number of instruments to analyze. Set to None for no limit.
VERBOSE = True  # Set to True for detailed output during analysis

def get_crypto_symbols():
    """
    Fetch a list of cryptocurrency symbols using CoinGecko API.
    Returns an empty list on failure.
    """
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": False
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        symbols = [f"{coin['symbol'].upper()}-USD" for coin in data]
        return symbols[:MAX_INSTRUMENTS_TO_ANALYZE]
    except Exception as e:
        if VERBOSE:
            print(f"Error fetching crypto symbols: {str(e)}")
        return []

def get_stock_symbols():
    """
    Fetch stock symbols from major indices using yfinance.
    Returns an empty list on failure.
    """
    indices = {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ",
        "^RUT": "Russell 2000"
    }
    symbols = set()
    for index, name in indices.items():
        try:
            index_data = yf.Ticker(index)
            components = index_data.info.get('components', [])
            if not components:
                print(f"No components found for {name}. Trying to fetch top holdings...")
                holdings = index_data.info.get('holdings', [])
                components = [holding.get('symbol') for holding in holdings if holding.get('symbol')]
            symbols.update(components)
            if VERBOSE:
                print(f"Fetched {len(components)} symbols from {name}")
        except Exception as e:
            if VERBOSE:
                print(f"Error fetching symbols for {name}: {str(e)}")
    return list(symbols)[:MAX_INSTRUMENTS_TO_ANALYZE]

def get_financial_data(symbol, start_date, end_date):
    """
    Fetch financial data (open, high, low, close) for a given symbol and date range using yfinance.
    Returns an empty DataFrame on failure.
    """
    try:
        data = yf.download(symbol, start=start_date, end=end_date)
        if data.empty:
            if VERBOSE:
                print(f"No data available for {symbol}")
            return pd.DataFrame()
        return data[['Open', 'High', 'Low', 'Close']]
    except Exception as e:
        if VERBOSE:
            print(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()

def calculate_weekly_fluctuation(data):
    """
    Calculate weekly price fluctuations as a percentage.
    """
    weekly_data = data.resample('W').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last'
    })
    return ((weekly_data['High'] - weekly_data['Low']) / weekly_data['Open']) * 100

def check_consecutive_fluctuations(fluctuations):
    """
    Check if there are 'CONSECUTIVE_WEEKS' of fluctuations between 'MIN_FLUCTUATION' and 'MAX_FLUCTUATION'.
    """
    count = 0
    for fluctuation in fluctuations:
        if MIN_FLUCTUATION <= fluctuation <= MAX_FLUCTUATION:
            count += 1
            if count == CONSECUTIVE_WEEKS:
                return True
        else:
            count = 0
    return False

def analyze_instrument(symbol):
    """
    Analyze a single financial instrument for the desired fluctuation pattern.
    Returns a dictionary with analysis results or None if no data is available.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=LOOKBACK_WEEKS)

    data = get_financial_data(symbol, start_date, end_date)
    if data.empty:
        return None

    fluctuations = calculate_weekly_fluctuation(data)
    if check_consecutive_fluctuations(fluctuations):
        last_close = data['Close'].iloc[-1]
        last_fluctuation = fluctuations.iloc[-1]
        return {
            'symbol': symbol,
            'last_close': last_close,
            'last_fluctuation': last_fluctuation,
            'average_fluctuation': fluctuations.mean()
        }
    return None

def analyze_instruments(instruments, instrument_type):
    """
    Analyze a list of financial instruments for the desired fluctuation pattern.
    Prints analysis summary and returns a list of dictionaries containing analysis results.
    """
    print(f"\nAnalyzing {instrument_type}...")
    print(f"Checking for {CONSECUTIVE_WEEKS} consecutive weeks of fluctuations "
          f"between {MIN_FLUCTUATION}% and {MAX_FLUCTUATION}%")

    results = []

    for i, instrument in enumerate(instruments, 1):
        result = analyze_instrument(instrument)
        if result:
            results.append(result)
        if VERBOSE:
            print(f"Processed {i}/{len(instruments)} {instrument_type}", end='\r')

    print(f"\n\nSummary for {instrument_type.capitalize()}:")
    print(f"Total {instrument_type} analyzed: {len(instruments)}")
    print(f"{instrument_type.capitalize()} meeting criteria: {len(results)}")

    if results:
        print(f"\nList of {instrument_type} meeting criteria:")
        for result in results:
            print(f"Symbol: {result['symbol']}")
            print(f"  Last Close: ${result['last_close']:.2f}")
            print(f"  Last Week's Fluctuation: {result['last_fluctuation']:.2f}%")
            print(f"  Average Weekly Fluctuation: {result['average_fluctuation']:.2f}%")
            print()
    else:
        print(f"\nNo {instrument_type} met the fluctuation criteria.")

    return results

def main():
    """
    Main function to run the analysis based on the configured parameters.
    """
    all_results = []

    if ANALYSIS_TYPE in ['crypto', 'both']:
        crypto_list = get_crypto_symbols()
        if crypto_list:
            crypto_results = analyze_instruments(crypto_list, "cryptocurrencies")
            all_results.extend(crypto_results)
        else:
            print("Failed to fetch cryptocurrency list. Please check your internet connection or try again later.")

    if ANALYSIS_TYPE in ['stocks', 'both']:
        stock_list = get_stock_symbols()
        if stock_list:
            stock_results = analyze_instruments(stock_list, "stocks")
            all_results.extend(stock_results)
        else:
            print("Failed to fetch stock list. Please check your internet connection or try again later.")

    if all_results:
        print("\nTop opportunities based on recent weekly fluctuations:")
        sorted_results = sorted(all_results, key=lambda x: x['last_fluctuation'], reverse=True)
        for result in sorted_results[:10]:  # Display top 10 opportunities
            print(f"Symbol: {result['symbol']}")
            print(f"  Last Close: ${result['last_close']:.2f}")
            print(f"  Last Week's Fluctuation: {result['last_fluctuation']:.2f}%")
            print(f"  Average Weekly Fluctuation: {result['average_fluctuation']:.2f}%")
            print()
    else:
        print("No results found. Please check your internet connection and try again.")

if __name__ == "__main__":
    main()