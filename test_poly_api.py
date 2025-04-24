import requests
import json

GAMMA_API = "https://gamma-api.polymarket.com"

def get_active_open_markets(limit=30):
    # Adds `closed=false` to avoid resolved markets
    url = f"{GAMMA_API}/markets?active=true&closed=false&limit={limit}"
    print(f"📡 Fetching markets from: {url}")
    response = requests.get(url)

    print(f"🔁 Response status code: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"❌ Failed to fetch: {response.status_code}")

    data = response.json()
    print(f"📦 Total markets received: {len(data)}")
    return data


def scan_for_arbitrage(markets, show_raw=False):
    print(f"\n🔎 Scanning {len(markets)} active + open markets...\n")
    arb_count = 0
    skipped_count = 0
    processed_count = 0

    for i, market in enumerate(markets):
        try:
            print(f"\n📍 Market #{i + 1} ---------------------------")

            if show_raw:
                print(json.dumps(market, indent=2))

            question = market.get("question", "Unknown")
            outcomes = market.get("outcomes", [])
            prices = market.get("outcomePrices", [])

            # 🔧 Handle stringified lists
            if isinstance(outcomes, str):
                outcomes = json.loads(outcomes)
            if isinstance(prices, str):
                prices = json.loads(prices)

            print(f"🧠 Question: {question}")
            print(f"📊 Parsed outcomes: {outcomes}")
            print(f"📈 Parsed prices: {prices}")
            print(f"📏 Lengths: outcomes = {len(outcomes)}, prices = {len(prices)}")

            if not outcomes or not prices:
                print("⚠️  Skipping: Empty outcomes or prices.")
                skipped_count += 1
                continue
            if len(outcomes) != len(prices):
                print("⚠️  Skipping: Mismatch in outcomes and prices.")
                skipped_count += 1
                continue

            prices_float = list(map(float, prices))

            total = sum(prices_float)

            print("📉 Outcome Prices:")
            for outcome, price in zip(outcomes, prices_float):
                print(f"   - {outcome}: {price:.3f}")

            print(f"💵 Total Cost of Full Coverage: {total:.4f}")

            if total < 1.0:
                print("💰 Arbitrage Opportunity Found!")
                arb_count += 1
            else:
                print("❌ No arbitrage (total >= 1.0)")

            processed_count += 1

        except Exception as e:
            print(f"❌ Error parsing market #{i + 1}: {e}")
            skipped_count += 1

    print(f"\n✅ Scan Complete")
    print(f"   Markets scanned: {len(markets)}")
    print(f"   Processed: {processed_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Arbitrage Opportunities Found: {arb_count}")

if __name__ == "__main__":
    markets = get_active_open_markets(limit=30)
    scan_for_arbitrage(markets, show_raw=False)
