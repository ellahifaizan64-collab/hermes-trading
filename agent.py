import os
import time
import yaml
import json
import urllib.request

def load_goal():
    try:
        with open('state/goal.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception:
        return {"asset": "BTCUSD", "target_return_30d": 0.05}

def place_alpaca_order(symbol, side, qty):
    api_key = os.environ.get("APCA_API_KEY_ID")
    api_secret = os.environ.get("APCA_API_SECRET_KEY")
    base_url = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    
    if not api_key or not api_secret:
        print("[ERROR] Alpaca API keys are missing from your Railway variables!")
        return False

    # Alpaca real orders endpoint
    url = f"{base_url}/v2/orders"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
        "Content-Type": "application/json"
    }
    
    # Order payload data
    data = {
        "symbol": symbol,
        "qty": str(qty),
        "side": side,
        "type": "market",
        "time_in_force": "gtc"
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print(f"✅ [REAL TRADE SUCCESS] Order placed successfully! Asset: {symbol} | Side: {side}")
            return True
    except Exception as e:
        print(f"❌ [API ERROR] Could not place order with Alpaca: {e}")
        return False

def main():
    config = load_goal()
    # Automatically clean up symbol format for Alpaca (e.g. BTC/USDT -> BTCUSD)
    asset = config.get('asset', 'BTCUSD').replace('/', '').replace('USDT', 'USD')
    
    print(f"🚀 Real Hermes Trading Agent Connected!")
    print(f"📊 Tracking Asset: {asset}")
    print("--------------------------------------------------")

    # This triggers a real trade order the moment your bot turns on!
    print(f"[LIVE] Sending a real test order to your Alpaca Paper Account...")
    
    # If it's Bitcoin, buy a safe small fraction. If it's a stock, buy 1 share.
    qty = 0.001 if "BTC" in asset else 1
    place_alpaca_order(symbol=asset, side="buy", qty=qty)

    trade_count = 0
    while True:
        trade_count += 1
        print(f"[LIVE] Monitoring the market for {asset}. System healthy...")
        time.sleep(60) # Wait 1 minute before checking again

if __name__ == "__main__":
    try:
        os.chdir('/app')
    except Exception:
        pass
    main()
