# Crypto and Stock Trading Research Suite

Welcome to the ultimate research toolkit for traders and investors! This comprehensive suite of applications, developed with Python, empowers you to make informed trading decisions in the world of cryptocurrencies and stocks.

# Crypto Watchdog

## Overview

The Crypto Investment Scanner is a Python application designed to identify promising cryptocurrency investment opportunities by monitoring trading volumes and price changes on Coinbase.

## Features

- **Data Fetching**: Retrieves cryptocurrency product information from the Coinbase API, focusing on USD pairs that are currently online.
- **Statistical Analysis**: Gathers statistics including trading volume, last price, and open price for performance assessment.
- **Investment Criteria**: Filters cryptocurrencies based on:
  - 24-hour trading volume greater than $1 million.
  - Price change exceeding 5% within the last 24 hours.
- **Concurrency**: Utilizes multithreading to efficiently fetch statistics for multiple currencies simultaneously.
- **Real-Time Monitoring**: Outputs a list of top promising cryptocurrencies every 5 minutes.

