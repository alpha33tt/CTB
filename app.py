import
from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Database setup and connection functions
def get_db_connection():
    conn = sqlite3.connect('wallets.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            address TEXT PRIMARY KEY, 
            exchange TEXT NOT NULL, 
            currency TEXT NOT NULL, 
            balance REAL NOT NULL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database (run this once)
create_db()

# Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/flash', methods=['POST'])
def flash_wallet():
    wallet_address = request.form['wallet_address']
    amount = float(request.form['amount'])
    exchange = request.form['exchange']
    currency = request.form['currency'].upper()

    # Validate exchange and currency
    if exchange not in ['binance', 'coinbase', 'bybit', 'trustwallet', 'exodus', 'luno']:
        return f"Error: Unsupported exchange '{exchange}'."
    if currency not in ['BTC', 'ETH', 'USDT']:
        return f"Error: Unsupported currency '{currency}' on exchange '{exchange}'."

    # Insert or update the wallet in the database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO wallets (address, exchange, currency, balance) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(address, exchange, currency) 
        DO UPDATE SET balance = balance + ?
    ''', (wallet_address, exchange, currency, 0.0, amount))
    conn.commit()
    conn.close()

    # Return the updated balance
    return f'Fake {currency} flashed successfully. New balance will be updated in the database.'

@app.route('/balance', methods=['GET'])
def get_balance():
    exchange = request.args.get('exchange').lower()
    currency = request.args.get('currency').upper()
    wallet_address = request.args.get('wallet_address')

    # Validate exchange and currency
    if exchange not in ['binance', 'coinbase', 'bybit', 'trustwallet', 'exodus', 'luno']:
        return f"Error: Unsupported exchange '{exchange}'."
    if currency not in ['BTC', 'ETH', 'USDT']:
        return f"Error: Unsupported currency '{currency}' on exchange '{exchange}'."

    # Retrieve the balance from the database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT balance FROM wallets WHERE address = ? AND exchange = ? AND currency = ?
    ''', (wallet_address, exchange, currency))
    result = c.fetchone()
    conn.close()

    if result:
        balance = result['balance']
        return f"Current balance for {currency} on {exchange.upper()} (Wallet: {wallet_address}): {balance}"
    else:
        return f"Error: Wallet address '{wallet_address}' not found."

@app.route('/modify_balance', methods=['POST'])
def modify_balance():
    exchange = request.form['exchange'].lower()  # e.g., 'binance'
    currency = request.form['currency'].upper()  # e.g., 'BTC'
    amount = float(request.form['amount'])  # Amount to add/subtract
    wallet_address = request.form['wallet_address']

    # Validate exchange and currency
    if exchange not in ['binance', 'coinbase', 'bybit', 'trustwallet', 'exodus', 'luno']:
        return f"Error: Unsupported exchange '{exchange}'."
    if currency not in ['BTC', 'ETH', 'USDT']:
        return f"Error: Unsupported currency '{currency}' on exchange '{exchange}'."

    # Modify the balance (add/subtract) in the database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE wallets SET balance = balance + ? WHERE address = ? AND exchange = ? AND currency = ?
    ''', (amount, wallet_address, exchange, currency))
    conn.commit()
    conn.close()

    # Return the updated balance
    return f"Balance for {currency} on {exchange.upper()} modified successfully. New balance: {amount} added."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
