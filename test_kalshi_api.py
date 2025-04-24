#!/usr/bin/env python3
import os
import time
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from clients import KalshiHttpClient, Environment

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def load_private_key(path: str, password: Optional[bytes] = None):
    """Load an RSA private key from PEM."""
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=password)

def make_client(env: Environment) -> KalshiHttpClient:
    """Instantiate the HTTP client using env vars DEMO_KEYID / DEMO_KEYFILE or PROD_*."""
    load_dotenv()
    key_id = os.getenv(f"{env.name}_KEYID") or ""
    key_file = os.getenv(f"{env.name}_KEYFILE") or ""
    priv = load_private_key(key_file)
    return KalshiHttpClient(key_id=key_id, private_key=priv, environment=env)

# -----------------------------------------------------------------------------
# 1) Fetch open markets
# -----------------------------------------------------------------------------

def get_open_markets(client: KalshiHttpClient, limit: int = 30) -> List[Dict[str, Any]]:
    """Call /markets to fetch only open (active & not closed) markets."""
    params = {
        "active": True,
        "closed": False,
        "limit": limit,
    }
    url = client.markets_url
    print(f"📡 Fetching open markets: GET {client.host}{url}  params={params}")
    resp = client.get(url, params=params)
    markets = resp.get("markets", [])
    print(f"🗃️  Received {len(markets)} markets.")
    return markets

# -----------------------------------------------------------------------------
# 2) Get most recent trade for a market
# -----------------------------------------------------------------------------

def get_latest_trade(client: KalshiHttpClient, ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch the single most recent trade for a given market ticker."""
    trades = client.get_trades(ticker=ticker, limit=1)
    items = trades.get("items") or trades.get("data") or []
    return items[0] if items else None

# -----------------------------------------------------------------------------
# 3) Scan for arbitrage
# -----------------------------------------------------------------------------

def scan_for_arbitrage(client: KalshiHttpClient, markets: List[Dict[str, Any]]):
    print(f"\n🔎 Scanning {len(markets)} markets for yes+no < 1.0 …\n")
    arb_count = 0

    for i, m in enumerate(markets, start=1):
        ticker = m["ticker"]
        title  = m.get("title", "")
        print(f"📍 Market #{i}: {ticker}")
        if title:
            print(f"   🧠 {title}")

        trade = get_latest_trade(client, ticker)
        if not trade:
            print("   ⚠️  No recent trades; skipping.")
            continue

        # Prices come back in cents
        yes_price = trade["yes_price"] / 100.0  
        no_price  = trade["no_price"]  / 100.0  

        total = yes_price + no_price
        print(f"   💵 yes={yes_price:.3f} + no={no_price:.3f} = total {total:.3f}")

        if total < 1.0:
            print("   🎉 Arbitrage opportunity!")
            arb_count += 1
        else:
            print("   ❌ No arbitrage (total ≥ 1.0)")

        # pause to respect rate limits
        time.sleep(0.1)

    print(f"\n✅ Scan complete. Arbitrage found: {arb_count}/{len(markets)}")

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # choose DEMO or PROD
    env    = Environment.DEMO
    client = make_client(env)

    # 1) Fetch
    markets = get_open_markets(client, limit=30)

    # 2) Scan
    scan_for_arbitrage(client, markets)
