import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import io

class AnalysisThread(QThread):
    update_progress = pyqtSignal(str)
    analysis_complete = pyqtSignal(list)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        self.update_progress.emit("Analysis started...")
        
        all_results = []

        if self.params['MANUAL_SYMBOLS']:
            self.update_progress.emit("Analyzing manually added symbols...")
            manual_results = self.analyze_instruments(self.params['MANUAL_SYMBOLS'], "manual symbols")
            all_results.extend(manual_results)

        if self.params['ANALYSIS_TYPE'] in ['crypto', 'both']:
            crypto_list = self.get_crypto_symbols()
            if crypto_list:
                self.update_progress.emit("Analyzing cryptocurrencies...")
                crypto_results = self.analyze_instruments(crypto_list, "cryptocurrencies")
                all_results.extend(crypto_results)
            else:
                self.update_progress.emit("Failed to fetch cryptocurrency list.")

        if self.params['ANALYSIS_TYPE'] in ['stocks', 'both']:
            stock_list = self.get_stock_symbols()
            if stock_list:
                self.update_progress.emit("Analyzing stocks...")
                stock_results = self.analyze_instruments(stock_list, "stocks")
                all_results.extend(stock_results)
            else:
                self.update_progress.emit("Failed to fetch stock list.")

        self.update_progress.emit("Analysis completed.")
        self.analysis_complete.emit(all_results)

    def get_crypto_symbols(self):
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
            return symbols[:self.params['MAX_INSTRUMENTS_TO_ANALYZE']]
        except Exception as e:
            self.update_progress.emit(f"Error fetching crypto symbols: {str(e)}")
            return []

    def get_stock_symbols(self):
        symbols = set()
        sp500 = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'BRK.B', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'NVDA']
        dow30 = ['AAPL', 'AMGN', 'AXP', 'BA', 'CAT', 'CRM', 'CSCO', 'CVX', 'DIS', 'DOW', 'GS', 'HD', 'HON', 'IBM', 'INTC']
        nasdaq100 = ['AAPL', 'MSFT', 'AMZN', 'TSLA', 'GOOGL', 'GOOG', 'FB', 'NVDA', 'PYPL', 'ADBE', 'NFLX', 'CMCSA', 'CSCO', 'PEP', 'AVGO']

        symbols.update(sp500)
        symbols.update(dow30)
        symbols.update(nasdaq100)

        try:
            url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"
            response = requests.get(url)
            response.raise_for_status()
            csv_data = io.StringIO(response.text)
            df = pd.read_csv(csv_data, header=None, names=['Symbol'])
            additional_symbols = df['Symbol'].tolist()
            symbols.update(additional_symbols)
        except Exception as e:
            self.update_progress.emit(f"Error fetching additional symbols: {str(e)}")

        return list(symbols)[:self.params['MAX_INSTRUMENTS_TO_ANALYZE']]

    def get_financial_data(self, symbol, start_date, end_date):
        try:
            data = yf.download(symbol, start=start_date, end=end_date)
            if data.empty:
                self.update_progress.emit(f"No data available for {symbol}")
                return pd.DataFrame()
            return data[['Open', 'High', 'Low', 'Close']]
        except Exception as e:
            self.update_progress.emit(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def calculate_weekly_fluctuation(self, data):
        weekly_data = data.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last'
        })
        return ((weekly_data['High'] - weekly_data['Low']) / weekly_data['Open']) * 100

    def check_consecutive_fluctuations(self, fluctuations):
        count = 0
        for fluctuation in fluctuations:
            if self.params['MIN_FLUCTUATION'] <= fluctuation <= self.params['MAX_FLUCTUATION']:
                count += 1
                if count == self.params['CONSECUTIVE_WEEKS']:
                    return True
            else:
                count = 0
        return False

    def analyze_instrument(self, symbol):
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=self.params['LOOKBACK_WEEKS'])

        data = self.get_financial_data(symbol, start_date, end_date)
        if data.empty:
            return None

        fluctuations = self.calculate_weekly_fluctuation(data)
        last_close = data['Close'].iloc[-1]
        last_fluctuation = fluctuations.iloc[-1]
        average_fluctuation = fluctuations.mean()
        
        return {
            'symbol': symbol,
            'last_close': last_close,
            'last_fluctuation': last_fluctuation,
            'average_fluctuation': average_fluctuation,
            'meets_criteria': self.check_consecutive_fluctuations(fluctuations)
        }

    def analyze_instruments(self, instruments, instrument_type):
        results = []
        for i, instrument in enumerate(instruments, 1):
            result = self.analyze_instrument(instrument)
            if result:
                results.append(result)
            if self.params['VERBOSE']:
                self.update_progress.emit(f"Processed {i}/{len(instruments)} {instrument_type}")
        return results

class FinancialAnalysisGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financial Instrument Analysis")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.create_input_section()
        self.create_output_section()

        self.analysis_thread = None

    def create_input_section(self):
        input_layout = QHBoxLayout()

        # Left column
        left_column = QVBoxLayout()
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(['crypto', 'stocks', 'both'])
        left_column.addWidget(QLabel("Analysis Type:"))
        left_column.addWidget(self.analysis_type)

        self.min_fluctuation = QDoubleSpinBox()
        self.min_fluctuation.setRange(0, 100)
        self.min_fluctuation.setValue(5)
        left_column.addWidget(QLabel("Min Fluctuation (%):"))
        left_column.addWidget(self.min_fluctuation)

        self.max_fluctuation = QDoubleSpinBox()
        self.max_fluctuation.setRange(0, 100)
        self.max_fluctuation.setValue(10)
        left_column.addWidget(QLabel("Max Fluctuation (%):"))
        left_column.addWidget(self.max_fluctuation)

        # Right column
        right_column = QVBoxLayout()
        self.consecutive_weeks = QSpinBox()
        self.consecutive_weeks.setRange(1, 52)
        self.consecutive_weeks.setValue(3)
        right_column.addWidget(QLabel("Consecutive Weeks:"))
        right_column.addWidget(self.consecutive_weeks)

        self.lookback_weeks = QSpinBox()
        self.lookback_weeks.setRange(1, 52)
        self.lookback_weeks.setValue(12)
        right_column.addWidget(QLabel("Lookback Weeks:"))
        right_column.addWidget(self.lookback_weeks)

        self.max_instruments = QSpinBox()
        self.max_instruments.setRange(1, 1000)
        self.max_instruments.setValue(800)
        right_column.addWidget(QLabel("Max Instruments:"))
        right_column.addWidget(self.max_instruments)

        # Add columns to input layout
        input_layout.addLayout(left_column)
        input_layout.addLayout(right_column)

        # Manual symbols input
        manual_symbols_layout = QHBoxLayout()
        self.manual_symbols_input = QLineEdit()
        manual_symbols_layout.addWidget(QLabel("Manual Symbols:"))
        manual_symbols_layout.addWidget(self.manual_symbols_input)

        # Verbose checkbox
        self.verbose_checkbox = QCheckBox("Verbose Output")

        # Start analysis button
        self.start_button = QPushButton("Start Analysis")
        self.start_button.clicked.connect(self.start_analysis)

        # Add all input widgets to main layout
        self.layout.addLayout(input_layout)
        self.layout.addLayout(manual_symbols_layout)
        self.layout.addWidget(self.verbose_checkbox)
        self.layout.addWidget(self.start_button)

    def create_output_section(self):
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.layout.addWidget(self.output_text)

    def start_analysis(self):
        self.start_button.setEnabled(False)
        self.output_text.clear()

        params = {
            'ANALYSIS_TYPE': self.analysis_type.currentText(),
            'MIN_FLUCTUATION': self.min_fluctuation.value(),
            'MAX_FLUCTUATION': self.max_fluctuation.value(),
            'CONSECUTIVE_WEEKS': self.consecutive_weeks.value(),
            'LOOKBACK_WEEKS': self.lookback_weeks.value(),
            'MAX_INSTRUMENTS_TO_ANALYZE': self.max_instruments.value(),
            'VERBOSE': self.verbose_checkbox.isChecked(),
            'MANUAL_SYMBOLS': [s.strip() for s in self.manual_symbols_input.text().split(',') if s.strip()]
        }

        self.analysis_thread = AnalysisThread(params)
        self.analysis_thread.update_progress.connect(self.update_output)
        self.analysis_thread.analysis_complete.connect(self.display_results)
        self.analysis_thread.start()

    def update_output(self, message):
        self.output_text.append(message)

    def display_results(self, results):
        self.output_text.append("\nAnalysis Results:")
        
        meeting_criteria = [r for r in results if r['meets_criteria']]
        
        self.output_text.append(f"\nTotal instruments analyzed: {len(results)}")
        self.output_text.append(f"Instruments meeting criteria: {len(meeting_criteria)}")
        
        if meeting_criteria:
            self.output_text.append("\nTop opportunities based on recent weekly fluctuations:")
            sorted_results = sorted(meeting_criteria, key=lambda x: x['last_fluctuation'], reverse=True)
            for result in sorted_results[:10]:  # Display top 10 opportunities
                self.output_text.append(f"\nSymbol: {result['symbol']}")
                self.output_text.append(f"  Last Close: ${result['last_close']:.2f}")
                self.output_text.append(f"  Last Week's Fluctuation: {result['last_fluctuation']:.2f}%")
                self.output_text.append(f"  Average Weekly Fluctuation: {result['average_fluctuation']:.2f}%")
        else:
            self.output_text.append("\nNo instruments met the fluctuation criteria.")

        self.start_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinancialAnalysisGUI()
    window.show()
    sys.exit(app.exec_())