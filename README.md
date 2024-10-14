# Crypto and Stock Trading Research Suite

Welcome to the ultimate research toolkit for traders and investors! This comprehensive suite of applications, developed with Python, empowers you to make informed trading decisions in the world of cryptocurrencies and stocks.

# Crypto Watchdog

## Overview

The Crypto Watchdog is a Python application designed to identify promising cryptocurrency investment opportunities by monitoring trading volumes and price changes on Coinbase.

## Features

- **Data Fetching**: Retrieves cryptocurrency product information from the Coinbase API, focusing on USD pairs that are currently online.
- **Statistical Analysis**: Gathers statistics including trading volume, last price, and open price for performance assessment.
- **Investment Criteria**: Filters cryptocurrencies based on:
  - 24-hour trading volume greater than $1 million.
  - Price change exceeding 5% within the last 24 hours.
- **Concurrency**: Utilizes multithreading to efficiently fetch statistics for multiple currencies simultaneously.
- **Real-Time Monitoring**: Outputs a list of top promising cryptocurrencies every 5 minutes.

- ## Requirements

- Python 3.x
- `requests` library (install via `pip install requests`)






# Fluctuation Finder

## Overview

The Fluctuation Finder is a Python application that analyzes stocks and cryptocurrencies for specific price fluctuation patterns over a defined period. The tool helps identify potential investment opportunities based on historical price movements.

## Features

- **Flexible Analysis**: Choose to analyze cryptocurrencies, stocks, or both.
- **Configurable Parameters**: Adjust the minimum and maximum fluctuation percentages, the number of consecutive weeks to check, and the lookback period for analysis.
- **Data Retrieval**: Fetches cryptocurrency symbols using the CoinGecko API and stock symbols from predefined lists and a comprehensive CSV file.
- **Fluctuation Calculation**: Calculates weekly price fluctuations and checks for patterns that meet defined criteria.
- **Verbose Output**: Provides detailed output during analysis for better tracking.

## Requirements

- Python 3.x
- `yfinance` library (install via `pip install yfinance`)
- `pandas` library (install via `pip install pandas`)
- `requests` library (install via `pip install requests`)

## Configuration

You can modify the following parameters in the code to customize your analysis:

- `ANALYSIS_TYPE`: Choose to analyze `'crypto'`, `'stocks'`, or `'both'`.
- `MIN_FLUCTUATION`: Minimum percentage fluctuation to consider (default is 2%).
- `MAX_FLUCTUATION`: Maximum percentage fluctuation to consider (default is 10%).
- `CONSECUTIVE_WEEKS`: Number of consecutive weeks to check for fluctuations (default is 3).
- `LOOKBACK_WEEKS`: Number of weeks to look back for analysis (default is 12).
- `MAX_INSTRUMENTS_TO_ANALYZE`: Maximum number of instruments to analyze (default is 20).
- `VERBOSE`: Set to `True` for detailed output during analysis.
- `MANUAL_SYMBOLS`: Add your manual stock or crypto symbols here (e.g., `['AAPL', 'GOOGL', 'BTC-USD']`).


