import os
import time
import json
import urllib.request
import random

# Global strategy parameters that the bot will automatically tune over time
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
        if s_ema > l_ema and balance > 0:
            shares = balance / cur_p
            balance = 0.0
        elif s_ema < l_ema and shares > 0:
            balance = shares * cur_p
            shares = 0.0
    return balance + (shares * prices[-1]) - 10000.0

def run_reflection_cycle(symbol):
    global CONFIG
    print("\n🧠 [HERMES REFLECTION CYCLE] Studying recent history to optimize strategy...")
    bars = get_crypto_bars(symbol, limit=100)
    if not bars or len(bars) < 30:
        print("⚠️ Insufficient data to study. Skipping reflection.")
        return
    
    best_profit = -99999.0
    best_cfg = CONFIG.copy()
    
    # AI Simulation Block: Try 35 random strategic adjustments to find the best one
    for _ in range(35):
        t_short = random.randint(3, 10)
        t_long = random.randint(15, 35)
        t_rsi_b = random.randint(30, 45)
        t_rsi_s = random.randint(55, 70)
        
        profit = simulate_strategy(bars, t_short, t_long, t_rsi_b, t_rsi_s)
        if profit > best_profit:
            best_profit = profit
            best_cfg = {"short_window": t_short, "long_window": t_long, "rsi_buy": t_rsi_b, "rsi_sell": t_rsi_s}
            
    print(f"📋 Reflection complete. Best simulated result: ${best_profit:,.2f}")
    if best_cfg != CONFIG:
        print(f"⚙️ Adapting rules to match market conditions:")
        print(f"   • Short Window: {CONFIG['short_window']} -> {best_cfg['short_window']}")
        print(f"   • Long Window: {CONFIG['long_window']} -> {best_cfg['long_window']}")
        CONFIG = best_cfg
    else:
        print("📊 Current settings remain optimal. No changes needed.")
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
            
            print(f"🏷️ {asset}: ${current_price:,.2f} | Short Window: {CONFIG['short_window']} | Long Window: {CONFIG['long_window']} | RSI: {rsi:.1f}")
            qty = get_current_position(base_url, asset)
            
            # Use the continuously adapted parameters to trade
            if short_ema > long_ema and rsi < CONFIG["rsi_sell"] and qty == 0:
                print("🚦 STRATEGY SIGNAL: Upward momentum detected. Placing BUY order...")
                place_alpaca_order(base_url, asset, "buy", 0.001)
            elif short_ema < long_ema and qty > 0:
                print("🚦 STRATEGY SIGNAL: Downward trend detected. Placing SELL order...")
                place_alpaca_order(base_url, asset, "sell", qty)
            else:
                print("⏳ Status: Conditions neutral. Holding position.")
                
        # Trigger the true reflection loop every 15 minutes
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
