"""Simple BTC/USD historical market analyzer using public CoinGecko data."""
import argparse
from datetime import datetime, timezone
import requests
import pandas as pd
import matplotlib.pyplot as plt

API = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart'


def fetch_prices(days: int) -> pd.DataFrame:
    response = requests.get(API, params={'vs_currency': 'usd', 'days': days}, timeout=25)
    response.raise_for_status()
    points = response.json()['prices']
    if not points:
        raise ValueError('No prices returned by API')
    df = pd.DataFrame(points, columns=['timestamp_ms', 'price_usd'])
    df['date'] = pd.to_datetime(df['timestamp_ms'], unit='ms', utc=True)
    df = df.set_index('date')[['price_usd']].resample('1D').last().dropna()
    return df


def main():
    parser = argparse.ArgumentParser(description='Analyze Bitcoin prices in USD')
    parser.add_argument('--days', type=int, default=30, choices=[7, 14, 30, 90, 180, 365])
    args = parser.parse_args()
    try:
        df = fetch_prices(args.days)
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise SystemExit(f'Unable to load market data: {exc}')
    if len(df) < 2:
        raise SystemExit('Not enough data for analysis')
    daily_returns = df['price_usd'].pct_change().dropna()
    change_pct = (df['price_usd'].iloc[-1] / df['price_usd'].iloc[0] - 1) * 100
    volatility = daily_returns.std() * (365 ** 0.5) * 100 if len(daily_returns) > 1 else float('nan')
    print(f'Period: {df.index[0].date()} to {df.index[-1].date()} (UTC)')
    print(f'Latest BTC price: ${df["price_usd"].iloc[-1]:,.2f}')
    print(f'Period change: {change_pct:+.2f}%')
    print(f'Annualized historical volatility: {volatility:.2f}%')
    df.to_csv('btc_prices.csv')
    ax = df['price_usd'].plot(figsize=(10, 5), title='Bitcoin price (USD)')
    ax.set_xlabel('Date (UTC)')
    ax.set_ylabel('USD')
    plt.tight_layout()
    plt.savefig('btc_chart.png', dpi=160)
    print('Saved btc_prices.csv and btc_chart.png')


if __name__ == '__main__':
    main()
