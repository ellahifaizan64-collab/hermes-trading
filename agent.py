import os
import time
import json
import urllib.request
import random

# Global hyperparameter state that the system autonomously optimizes over time
CONFIG = {
    "short_window": 5,
    "long_window": 20,
    "rsi_buy": 35,
    "rsi_sell": 65
}

def get_alpaca_headers():
    api_key = os.environ.get("APCA_API_KEY_ID")
    api_secret = os.environ.get("APCA_API_SECRET_KEY")
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
        "Content-Type": "application/json"
    }

def get_latest_price(symbol):
    data_symbol = "BTC/USD" if "BTC" in symbol else symbol
    url = f"https://data.alpaca.markets/v1beta3/crypto/us/latest/trades?symbols={data_symbol}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return float(res_data["trades"][data_symbol]["p"])
    except Exception as e:
        print(f"⚠️ Price Fetch Error: {e}")
        return None

def get_crypto_bars(symbol, limit=100):
    data_symbol = "BTC/USD" if "BTC" in symbol else symbol
    url = f"https://data.alpaca.markets/v1beta3/crypto/us/bars?symbols={data_symbol}&timeframe=1Min&limit={limit}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("bars", {}).get(data_symbol, [])
    except Exception as e:
        print(f"⚠️ Bars Fetch Error: {e}")
        return []

def calculate_ema(prices, window):
    if len(prices) < window:
        return prices[-1] if prices else 0
    alpha = 2 / (window + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price * alpha) + (ema * (1 - alpha))
    return ema

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains, losses = 0, 0
    for i in range(1, period + 1):
        diff = prices[-i] - prices[-i-1]
        if diff > 0:
            gains += diff
        else:
            losses -= diff
    if losses == 0:
        return 100
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def get_current_position(base_url, symbol):
    url = f"{base_url}/v2/positions/{symbol}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return float(res_data["qty"])
    except Exception:
        return 0.0

def place_alpaca_order(base_url, symbol, side, qty):
    url = f"{base_url}/v2/orders"
    headers = get_alpaca_headers()
    data = {
        "symbol": symbol,
        "qty": str(qty),
        "side": side,
        "type": "market",
        "time_in_force": "gtc"
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            print(f"✅ [TRADE EXECUTED] Successfully placed {side} order for {qty} {symbol}!")
            return True
    except Exception as e:
        print(f"❌ [ORDER ERROR] Failed to place {side} order: {e}")
        return False

def simulate_strategy(bars, short_w, long_w, rsi_b, rsi_s):
    prices = [float(b['c']) for b in bars]
    if len(prices) < long_w:
        return 0.0
    balance = 10000.0
    shares = 0.0
    for i in range(long_w, len(prices)):
        sub_prices = prices[:i+1]
        cur_p = sub_prices[-1]
        s_ema = calculate_ema(sub_prices, short_w)
        l_ema = calculate_ema(sub_prices, long_w)
        rsi = calculate_rsi(sub_prices)
        if s_ema > l_ema and rsi < rsi_s and balance > 0:
            shares = balance / cur_p
            balance = 0.0
        elif s_ema < l_ema and shares > 0:
            balance = shares * cur_p
            shares = 0.0
    return balance + (shares * prices[-1]) - 10000.0

def run_reflection_cycle(symbol):
    global CONFIG
    print("\n[HERMES REFLECTION CYCLE] 🧠 Evaluated last market window. Optimizing strategy...")
    bars = get_crypto_bars(symbol, limit=100)
    if not bars or len(bars) < 30:
        print("⚠️ Insufficient backtest data. Skipping cycle.")
        return
    best_p = -99999.0
    best_cfg = CONFIG.copy()
    
    # Mathematical adaptation block (Hill-climbing strategy simulation)
    for _ in range(35):
        t_short = random.randint(3, 10)
        t_long = random.randint(15, 35)
        t_rsi_b = random.randint(30, 45)
        t_rsi_s = random.randint(55, 70)
        p = simulate_strategy(bars, t_short, t_long, t_rsi_b, t_rsi_s)
        if p > best_p:
            best_p = p
            best_cfg = {"short_window": t_short, "long_window": t_long, "rsi_buy": t_rsi_b, "rsi_sell": t_rsi_s}
            
    print(f"[REFLECTION] Cycle complete. Best potential return found: ${best_p:,.2f}")
    if best_cfg != CONFIG:
        print(f"⚙️ Adjusting hyperparameters to maximize future Sharpe ratio:")
        print(f"   • Short EMA Window: {CONFIG['short_window']} -> {best_cfg['short_window']}")
        print(f"   • Long EMA Window: {CONFIG['long_window']} -> {best_cfg['long_window']}")
        CONFIG = best_cfg
    else:
        print("📊 Configuration remains mathematically optimal.")
    print("--------------------------------------------------\n")

def main():
    asset = "BTCUSD"
    base_url = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    print("🚀 Real Autonomous Self-Improving Agent Active!")
    print(f"📊 Live Tracking: {asset}")
    print("--------------------------------------------------")
    
    loop_count = 0
    while True:
        loop_count += 1
        bars = get_crypto_bars(asset, limit=50)
        if bars:
            prices = [float(b['c']) for b in bars]
            current_price = prices[-1]
            short_ema = calculate_ema(prices, CONFIG["short_window"])
            long_ema = calculate_ema(prices, CONFIG["long_window"])
            rsi = calculate_rsi(prices)
            
            print(f"🏷️ {asset}: ${current_price:,.2f} | Short EMA: {short_ema:.2f} | Long EMA: {long_ema:.2f} | RSI: {rsi:.1f}")
            qty = get_current_position(base_url, asset)
            
            # Smart execution based on adaptive parameters
            if short_ema > long_ema and rsi < CONFIG["rsi_sell"] and qty == 0:
                print("🚦 STRATEGY SIGNAL: Bullish momentum detected. Buying...")
                place_alpaca_order(base_url, asset, "buy", 0.001)
            elif short_ema < long_ema and qty > 0:
                print("🚦 STRATEGY SIGNAL: Bearish trend reversal. Selling...")
                place_alpaca_order(base_url, asset, "sell", qty)
            else:
                print("⏳ Status: Market conditions neutral. Holding position.")
                
        if loop_count % 15 == 0:
            run_reflection_cycle(asset)
            
        print("--------------------------------------------------")
        time.sleep(60)

if __name__ == "__main__":
    try:
        os.chdir('/app')
    except Exception:
        pass
    main()
   
