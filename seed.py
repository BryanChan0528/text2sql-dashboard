"""Seed the SQLite database with realistic Deriv-style sample data."""

import random
import sqlite3
from datetime import datetime, timedelta
from schema import init_db, get_connection

COUNTRIES = [
    "Malaysia", "Indonesia", "Nigeria", "Kenya", "Brazil",
    "South Africa", "India", "Vietnam", "Philippines", "Thailand",
]

SYMBOLS_DATA = [
    ("EURUSD", "forex", "EUR/USD"),
    ("GBPUSD", "forex", "GBP/USD"),
    ("USDJPY", "forex", "USD/JPY"),
    ("AUDUSD", "forex", "AUD/USD"),
    ("BTCUSD", "crypto", "BTC/USD"),
    ("ETHUSD", "crypto", "ETH/USD"),
    ("XAUUSD", "commodities", "Gold/USD"),
    ("XAGUSD", "commodities", "Silver/USD"),
    ("US500", "indices", "S&P 500"),
    ("US30", "indices", "Dow Jones"),
    ("UK100", "indices", "FTSE 100"),
    ("DE40", "indices", "DAX 40"),
]

ACCOUNT_TYPES = ["real", "demo"]
SIDES = ["buy", "sell"]


def seed():
    init_db()

    with get_connection() as conn:
        # Skip if already seeded
        count = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        if count > 0:
            print(f"DB already has {count} trades — skipping seed.")
            return

        # Insert symbols
        conn.executemany(
            "INSERT OR IGNORE INTO symbols VALUES (?, ?, ?)",
            SYMBOLS_DATA,
        )

        # Insert clients
        rng = random.Random(42)
        base_date = datetime(2024, 1, 1)
        clients = []
        for i in range(1, 301):
            country = rng.choice(COUNTRIES)
            acct = rng.choice(ACCOUNT_TYPES)
            days_offset = rng.randint(0, 364)
            signup = (base_date + timedelta(days=days_offset)).date().isoformat()
            clients.append((i, country, acct, signup))

        conn.executemany(
            "INSERT OR IGNORE INTO clients VALUES (?, ?, ?, ?)",
            clients,
        )

        # Insert trades
        symbols = [s[0] for s in SYMBOLS_DATA]
        trades = []
        start_ts = datetime(2024, 1, 1)

        for i in range(1, 2001):
            client_id = rng.randint(1, 300)
            symbol = rng.choice(symbols)
            side = rng.choice(SIDES)
            amount = round(rng.uniform(10, 500), 2)
            # profit: roughly normal, skewed slightly negative (house edge)
            profit = round(rng.gauss(-0.5, amount * 0.8), 2)
            duration = rng.randint(30, 3600)
            days_offset = rng.randint(0, 364)
            hours_offset = rng.randint(0, 23)
            ts = (start_ts + timedelta(days=days_offset, hours=hours_offset)).isoformat()
            trades.append((i, client_id, symbol, side, amount, profit, duration, ts))

        conn.executemany(
            "INSERT OR IGNORE INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            trades,
        )

        print(f"Seeded: {len(clients)} clients, {len(trades)} trades, {len(SYMBOLS_DATA)} symbols.")


if __name__ == "__main__":
    seed()
