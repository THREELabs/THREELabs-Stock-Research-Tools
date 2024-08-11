import sys
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import random
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTextEdit, QTabWidget,
                             QProgressBar, QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

def get_stock_data(ticker, period="1mo"):
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        return stock, history
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_weekly_change(history):
    weekly_returns = history['Close'].resample('W').last().pct_change()
    return weekly_returns.mean()

def get_recommendations(history, avg_weekly_change, min_fluctuation, max_fluctuation):
    current_price = history['Close'].iloc[-1]

    # Use the user-defined fluctuation range
    buy_price = current_price * (1 - max_fluctuation / 100)
    sell_price = current_price * (1 + min_fluctuation / 100)

    return buy_price, sell_price

def analyze_stock(ticker, min_fluctuation, max_fluctuation):
    stock, history = get_stock_data(ticker)
    if stock is None or history is None or history.empty or len(history) < 14:
        return None

    history['RSI'] = calculate_rsi(history)
    history['SMA_50'] = history['Close'].rolling(window=50).mean()
    history['SMA_200'] = history['Close'].rolling(window=200).mean()

    current_price = history['Close'].iloc[-1]
    current_rsi = history['RSI'].iloc[-1]
    sma_50 = history['SMA_50'].iloc[-1]
    sma_200 = history['SMA_200'].iloc[-1]

    if current_rsi < 40 and current_price > sma_50 * 0.95:
        avg_weekly_change = analyze_weekly_change(history)
        buy_price, sell_price = get_recommendations(history, avg_weekly_change, min_fluctuation, max_fluctuation)

        potential_gain_percentage = ((sell_price / buy_price) - 1) * 100
        potential_gain_dollars = (sell_price - buy_price)

        return {
            'ticker': ticker,
            'current_price': current_price,
            'rsi': current_rsi,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'potential_gain_percentage': potential_gain_percentage,
            'potential_gain_dollars': potential_gain_dollars
        }

    return None

def get_tickers(num_stocks):
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    tables = pd.read_html(response.text)
    sp500_table = tables[0]
    tickers = sp500_table['Symbol'].tolist()
    return random.sample(tickers, min(num_stocks, len(tickers)))

class StockAnalysisWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, tickers, min_fluctuation, max_fluctuation):
        super().__init__()
        self.tickers = tickers
        self.min_fluctuation = min_fluctuation
        self.max_fluctuation = max_fluctuation

    def run(self):
        promising_stocks = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(analyze_stock, ticker, self.min_fluctuation, self.max_fluctuation): ticker for ticker in self.tickers}
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                if result:
                    promising_stocks.append(result)
                self.progress.emit(int(i / len(self.tickers) * 100))

        self.finished.emit(promising_stocks)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Analysis Tool")
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Single Stock Analysis Tab
        single_stock_tab = QWidget()
        tabs.addTab(single_stock_tab, "Single Stock Analysis")
        self.setup_single_stock_tab(single_stock_tab)

        # Multiple Stocks Analysis Tab
        multiple_stocks_tab = QWidget()
        tabs.addTab(multiple_stocks_tab, "Multiple Stocks Analysis")
        self.setup_multiple_stocks_tab(multiple_stocks_tab)

        print("MainWindow initialized")  # Debug print

    def setup_single_stock_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Ticker input
        ticker_layout = QHBoxLayout()
        ticker_label = QLabel("Enter stock ticker:")
        self.ticker_input = QLineEdit()
        ticker_layout.addWidget(ticker_label)
        ticker_layout.addWidget(self.ticker_input)

        # Fluctuation percentage input
        fluctuation_layout = QHBoxLayout()
        fluctuation_label = QLabel("Price fluctuation range (%):")
        self.min_fluctuation_input_single = QDoubleSpinBox()
        self.min_fluctuation_input_single.setRange(0.1, 100)
        self.min_fluctuation_input_single.setValue(4.0)
        self.min_fluctuation_input_single.setSingleStep(0.1)
        self.max_fluctuation_input_single = QDoubleSpinBox()
        self.max_fluctuation_input_single.setRange(0.1, 100)
        self.max_fluctuation_input_single.setValue(8.0)
        self.max_fluctuation_input_single.setSingleStep(0.1)
        fluctuation_layout.addWidget(fluctuation_label)
        fluctuation_layout.addWidget(self.min_fluctuation_input_single)
        fluctuation_layout.addWidget(QLabel("to"))
        fluctuation_layout.addWidget(self.max_fluctuation_input_single)

        analyze_button = QPushButton("Analyze")
        analyze_button.clicked.connect(self.analyze_single_stock)
        fluctuation_layout.addWidget(analyze_button)

        layout.addLayout(ticker_layout)
        layout.addLayout(fluctuation_layout)

        # Results display
        self.single_stock_results = QTextEdit()
        self.single_stock_results.setReadOnly(True)
        layout.addWidget(self.single_stock_results)

    def setup_multiple_stocks_tab(self, tab):
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Number of stocks input
        num_stocks_layout = QHBoxLayout()
        num_stocks_label = QLabel("Number of stocks to analyze:")
        self.num_stocks_input = QSpinBox()
        self.num_stocks_input.setRange(1, 1000)
        self.num_stocks_input.setValue(100)
        num_stocks_layout.addWidget(num_stocks_label)
        num_stocks_layout.addWidget(self.num_stocks_input)

        # Fluctuation percentage input
        fluctuation_layout = QHBoxLayout()
        fluctuation_label = QLabel("Price fluctuation range (%):")
        self.min_fluctuation_input_multiple = QDoubleSpinBox()
        self.min_fluctuation_input_multiple.setRange(0.1, 100)
        self.min_fluctuation_input_multiple.setValue(4.0)
        self.min_fluctuation_input_multiple.setSingleStep(0.1)
        self.max_fluctuation_input_multiple = QDoubleSpinBox()
        self.max_fluctuation_input_multiple.setRange(0.1, 100)
        self.max_fluctuation_input_multiple.setValue(8.0)
        self.max_fluctuation_input_multiple.setSingleStep(0.1)
        fluctuation_layout.addWidget(fluctuation_label)
        fluctuation_layout.addWidget(self.min_fluctuation_input_multiple)
        fluctuation_layout.addWidget(QLabel("to"))
        fluctuation_layout.addWidget(self.max_fluctuation_input_multiple)

        analyze_button = QPushButton("Analyze")
        analyze_button.clicked.connect(self.analyze_multiple_stocks)
        fluctuation_layout.addWidget(analyze_button)

        layout.addLayout(num_stocks_layout)
        layout.addLayout(fluctuation_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Ticker", "Current Price", "RSI", "Buy Price", "Sell Price",
            "Potential Gain (%)", "Potential Gain ($)"
        ])
        layout.addWidget(self.results_table)

    def analyze_single_stock(self):
        ticker = self.ticker_input.text().strip().upper()
        min_fluctuation = self.min_fluctuation_input_single.value()
        max_fluctuation = self.max_fluctuation_input_single.value()
        if not ticker:
            self.single_stock_results.setText("Please enter a valid ticker symbol.")
            return

        self.single_stock_results.setText(f"Analyzing {ticker}...")
        QApplication.processEvents()

        stock, history = get_stock_data(ticker, period="1y")
        if stock is None or history is None or history.empty:
            self.single_stock_results.setText(f"Unable to fetch data for {ticker}")
            return

        info = stock.info
        current_price = history['Close'].iloc[-1]

        result = f"Stock Information for {ticker}:\n\n"
        result += f"Current Price: ${current_price:.2f}\n"
        result += f"52 Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}\n"
        result += f"52 Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}\n"
        result += f"Market Cap: ${info.get('marketCap', 0) / 1e9:.2f}B\n"
        result += f"P/E Ratio: {info.get('trailingPE', 'N/A')}\n"
        result += f"Dividend Yield: {info.get('dividendYield', 0) * 100:.2f}%\n\n"

        avg_weekly_change = analyze_weekly_change(history)
        result += f"Average Weekly Change: {avg_weekly_change:.2%}\n\n"

        last_week = history.last('1w')
        weekly_low = last_week['Low'].min()
        weekly_high = last_week['High'].max()
        weekly_change = (last_week['Close'].iloc[-1] / last_week['Open'].iloc[0] - 1)

        result += "Last Week's Performance:\n"
        result += f"Last Week's Low: ${weekly_low:.2f}\n"
        result += f"Last Week's High: ${weekly_high:.2f}\n"
        result += f"Last Week's Change: {weekly_change:.2%}\n\n"

        buy_price, sell_price = get_recommendations(history, avg_weekly_change, min_fluctuation, max_fluctuation)

        result += "Recommendations:\n"
        result += f"Recommended Buy Price: ${buy_price:.2f}\n"
        result += f"Recommended Sell Price: ${sell_price:.2f}\n"

        self.single_stock_results.setText(result)

    def analyze_multiple_stocks(self):
        num_stocks = self.num_stocks_input.value()
        min_fluctuation = self.min_fluctuation_input_multiple.value()
        max_fluctuation = self.max_fluctuation_input_multiple.value()
        self.progress_bar.setValue(0)
        self.results_table.setRowCount(0)
        QApplication.processEvents()

        tickers = get_tickers(num_stocks)
        if not tickers:
            self.results_table.setRowCount(1)
            self.results_table.setItem(0, 0, QTableWidgetItem("No tickers found. Please try again later."))
            return

        self.worker = StockAnalysisWorker(tickers, min_fluctuation, max_fluctuation)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.display_results)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_results(self, promising_stocks):
        promising_stocks.sort(key=lambda x: x['potential_gain_percentage'], reverse=True)
        self.results_table.setRowCount(len(promising_stocks))

        for i, stock in enumerate(promising_stocks):
            self.results_table.setItem(i, 0, QTableWidgetItem(stock['ticker']))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"${stock['current_price']:.2f}"))
            self.results_table.setItem(i, 2, QTableWidgetItem(f"{stock['rsi']:.2f}"))
            self.results_table.setItem(i, 3, QTableWidgetItem(f"${stock['buy_price']:.2f}"))
            self.results_table.setItem(i, 4, QTableWidgetItem(f"${stock['sell_price']:.2f}"))
            self.results_table.setItem(i, 5, QTableWidgetItem(f"{stock['potential_gain_percentage']:.2f}%"))
            self.results_table.setItem(i, 6, QTableWidgetItem(f"${stock['potential_gain_dollars']:.2f}"))

        self.results_table.resizeColumnsToContents()

def main():
    print("Starting application")  # Debug print
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    print("Window shown")  # Debug print
    sys.exit(app.exec())

if __name__ == "__main__":
    main()