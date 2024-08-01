# Stock Analysis Tools (Default In Out Script)

This Python program is a comprehensive stock analysis tool that provides users with the ability to analyze individual stocks and search for promising investment opportunities across a large number of stocks. The tool leverages financial data from Yahoo Finance and the NASDAQ API to perform various analyses and provide investment recommendations.

## Key Features:

1. **Single Stock Analysis**: 
   - Fetches detailed information about a specific stock, including current price, 52-week high/low, market cap, P/E ratio, and dividend yield.
   - Calculates and displays average weekly change and last week's performance.
   - Provides recommended buy and sell prices based on current market trends.

2. **Promising Stock Search**:
   - Allows users to specify the number of stocks to analyze (recommended: 100 to 1000).
   - Fetches a random selection of stock tickers from the NASDAQ API.
   - Analyzes each stock using multiple technical indicators:
     - Relative Strength Index (RSI)
     - Simple Moving Averages (50-day and 200-day)
     - Weekly price changes
   - Identifies promising stocks based on predefined criteria:
     - RSI below 40 (potentially oversold)
     - Current price above 95% of the 50-day moving average
   - Calculates potential gain percentages and dollar amounts for each promising stock.
   - Ranks and displays the top promising stocks based on potential gains.

3. **Technical Analysis**:
   - Calculates RSI (Relative Strength Index) to identify overbought or oversold conditions.
   - Computes 50-day and 200-day Simple Moving Averages (SMA) for trend analysis.
   - Analyzes weekly price changes to gauge stock volatility and momentum.

4. **Multithreading**:
   - Utilizes concurrent processing to analyze multiple stocks simultaneously, significantly reducing overall analysis time.

5. **User-Friendly Interface**:
   - Offers a simple command-line interface for easy interaction.
   - Provides clear options for single stock analysis or bulk stock search.
   - Displays results in a formatted, easy-to-read table format.

6. **Data Visualization** (commented out in the current version):
   - Includes commented code for potential integration of matplotlib for graphical representation of stock data.

## Technical Details:

- Written in Python
- Uses libraries such as yfinance, pandas, numpy, requests, and tabulate
- Implements error handling for API requests and data processing
- Employs multithreading for efficient processing of large datasets

This Stock Analysis Tool is designed to assist investors in making informed decisions by providing comprehensive stock data, technical analysis, and potential investment recommendations. It's important to note that all investment decisions should be made with careful consideration and additional research.


# Financial Instrument Fluctuation Analyzer (Default Drop Checker Script)

## Overview
This Python script is a versatile tool designed to analyze price fluctuations in financial instruments, specifically cryptocurrencies and stocks. It allows users to identify assets that have experienced significant price movements over a specified period, helping investors and analysts spot volatile or potentially interesting investment opportunities.

## Key Features
1. **Dual Analysis Capability**: Can analyze both cryptocurrencies and stocks, or focus on just one category.
2. **Customizable Parameters**: Users can easily adjust key parameters such as:
   - Type of analysis (crypto, stocks, or both)
   - Fluctuation threshold percentage
   - Number of weeks to analyze
   - Maximum number of instruments to analyze
3. **Dynamic Data Fetching**: Automatically retrieves up-to-date lists of cryptocurrencies and S&P 500 stocks.
4. **Flexible Output**: Offers both detailed and summary outputs, controllable via a verbose mode setting.

## How It Works
1. **Data Retrieval**:
   - Cryptocurrencies: Fetches from Yahoo Finance's cryptocurrency page.
   - Stocks: Retrieves the S&P 500 list from Wikipedia.

2. **Historical Data Analysis**:
   - Uses the `yfinance` library to fetch historical price data for each instrument.
   - Calculates weekly price fluctuations over the specified period.

3. **Fluctuation Check**:
   - Identifies instruments that have fluctuated by more than the specified threshold percentage every week for the set number of weeks.

4. **Results Presentation**:
   - Provides a summary of the analysis, including the total number of instruments analyzed and those meeting the fluctuation criteria.
   - In verbose mode, offers detailed progress updates and lists all instruments with significant fluctuations.

## Use Cases
- Identifying highly volatile cryptocurrencies or stocks for trading opportunities.
- Conducting market research to understand price movement patterns.
- Screening for potentially unstable investments to avoid or investigate further.
- Comparing volatility between crypto markets and traditional stock markets.

## Customization
The script is highly customizable through easy-to-edit parameters at the top of the file, allowing users to:
- Switch between analyzing cryptocurrencies, stocks, or both.
- Adjust the fluctuation threshold to find more or less volatile instruments.
- Change the analysis timeframe by modifying the number of weeks checked.
- Limit the number of instruments analyzed for quicker results.

## Requirements
- Python 3.x
- Libraries: yfinance, pandas, requests

## Note
This script is intended for informational and educational purposes only. It should not be considered as financial advice. Always conduct thorough research and consider consulting with a financial advisor before making investment decisions.
