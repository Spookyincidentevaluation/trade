from flask import Flask, render_template, jsonify
import random
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objs as go
from collections import deque

# Flask App Setup
flask_app = Flask(__name__)

# Simulating the market data and trading logic
class TradingBot:
    def __init__(self):
        self.balance = 10000  # Initial balance
        self.position = 0  # 0 = no trade, 1 = bought
        self.entry_price = 0
        self.trailing_stop_loss = 0
        self.trade_history = []
        self.market_prices = deque(maxlen=100)  # Store the last 100 prices for visualization
    
    def get_market_price(self):
        """Simulate real-time market price."""
        price = random.uniform(100, 200)  # Simulate price between 100 and 200
        self.market_prices.append(price)
        return price
    
    def place_trade(self, price, trade_type="buy"):
        """Place a trade: either 'buy' or 'sell'."""
        if trade_type == "buy" and self.position == 0:
            self.position = 1
            self.entry_price = price
            self.trailing_stop_loss = price * 0.98  # 2% trailing stop-loss
            self.balance -= price  # Deduct cost of the trade
            return f"Bought at ${price:.2f}"
        elif trade_type == "sell" and self.position == 1:
            self.position = 0
            profit = price - self.entry_price
            self.balance += price  # Add sale price to balance
            self.trade_history.append(profit)
            return f"Sold at ${price:.2f} for a profit of ${profit:.2f}"
        return "No trade executed."
    
    def manage_trade(self, current_price):
        """Manage ongoing trades and update stop-loss."""
        if self.position == 1:  # If a position is open
            # Adjust trailing stop-loss if price increases
            if current_price > self.entry_price:
                self.trailing_stop_loss = max(self.trailing_stop_loss, current_price * 0.98)
            
            # Trigger sell if price falls below trailing stop-loss
            if current_price < self.trailing_stop_loss:
                return self.place_trade(current_price, "sell")
        return "Holding position."

# Initialize the trading bot
trading_bot = TradingBot()

# Flask Route: Home Page
@flask_app.route('/')
def index():
    return "Trading Bot Demo: Visit /dashboard for the live dashboard."

# Flask API Route: Fetch Current Market Data
@flask_app.route('/api/market')
def market():
    current_price = trading_bot.get_market_price()
    status = trading_bot.manage_trade(current_price)
    return jsonify({
        'current_price': current_price,
        'balance': trading_bot.balance,
        'status': status,
        'trade_history': trading_bot.trade_history
    })

# Dash App for Visualization
dash_app = Dash(__name__, server=flask_app, url_base_pathname='/dashboard/')

# Dash Layout
dash_app.layout = html.Div([
    html.H1("Live Trading Bot Dashboard", style={'textAlign': 'center'}),
    dcc.Graph(id='live-chart', style={'height': '70vh'}),
    html.Div(id='trade-info', style={'textAlign': 'center', 'marginTop': '20px'}),
    dcc.Interval(id='update-interval', interval=1000, n_intervals=0)  # Update every second
])

# Dash Callback: Update Chart and Info
@dash_app.callback(
    [Output('live-chart', 'figure'), Output('trade-info', 'children')],
    [Input('update-interval', 'n_intervals')]
)
def update_dashboard(n):
    current_price = trading_bot.get_market_price()
    status = trading_bot.manage_trade(current_price)

    # Create line chart for market prices
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=list(trading_bot.market_prices),
        mode='lines',
        name='Market Price'
    ))
    fig.update_layout(title="Market Prices", xaxis_title="Time", yaxis_title="Price ($)")
    
    # Trade info display
    trade_info = f"Balance: ${trading_bot.balance:.2f} | Last Action: {status}"
    if trading_bot.trade_history:
        trade_info += f" | Total Profit: ${sum(trading_bot.trade_history):.2f}"
    
    return fig, trade_info

# Run Flask and Dash Apps
if __name__ == '__main__':
    flask_app.run(debug=False)
