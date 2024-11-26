import requests
import pandas as pd


BASE_URL = "https://api.binance.com/api/v3/klines"



def fetch_klines(symbol="BTCUSDT", interval="5m", limit=100):
    url = BASE_URL
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df[["timestamp", "open", "high", "low", "close", "volume"]]
    else:
        raise Exception(f"Error fetching klines: {response.status_code}, {response.text}")



def calculate_macd(df, fast=12, slow=26, signal=9):
    df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd"] = df["ema_fast"] - df["ema_slow"]
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df



def calculate_stoch_rsi(df, period=14):
    df["min_low"] = df["low"].rolling(window=period).min()
    df["max_high"] = df["high"].rolling(window=period).max()
    df["rsi"] = (df["close"] - df["min_low"]) / (df["max_high"] - df["min_low"])
    df["stoch_rsi_k"] = df["rsi"].rolling(window=3).mean() * 100
    df["stoch_rsi_d"] = df["stoch_rsi_k"].rolling(window=3).mean()
    return df



def predict_direction(df):
    latest_macd = df["macd"].iloc[-1]
    latest_signal = df["macd_signal"].iloc[-1]
    latest_close = df["close"].iloc[-1]
    previous_close = df["close"].iloc[-2]


    if latest_macd > latest_signal and latest_close > previous_close:
        return "Bullish (Yukarı Yönlü)"
    elif latest_macd < latest_signal and latest_close < previous_close:
        return "Bearish (Aşağı Yönlü)"
    else:
        return "Neutral (Yatay)"


def main():
    symbol = "BTCUSDT"
    timeframes = {"5m": "5 Dakika", "15m": "15 Dakika", "30m": "30 Dakika", "1h": "1 Saat"}
    results = {}

    print("Binance API Verileri ve Yön Tahmini:")

    for interval, description in timeframes.items():
        print(f"\n{description.upper()}:")

        klines = fetch_klines(symbol=symbol, interval=interval)


        klines = calculate_macd(klines)
        klines = calculate_stoch_rsi(klines)


        direction = predict_direction(klines)
        print(f"Yön Tahmini: {direction}")


        print(klines.tail(5))

        results[interval] = {"data": klines, "direction": direction}

    return results


if __name__ == "__main__":
    results = main()
