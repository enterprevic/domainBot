import aiohttp
import asyncio
import json
import os
import sys
import ssl

# Import base configuration
import config

# Try to import local configuration if it exists
if os.path.exists(os.path.join(os.path.dirname(__file__), 'config_local.py')):
    try:
        import config_local
        # Override base config with local config
        for key in dir(config_local):
            if not key.startswith('__'):
                setattr(config, key, getattr(config_local, key))
    except ImportError:
        print("Warning: config_local.py found but couldn't be imported")

# Check if API key is set
if config.RAPIDAPI_KEY == "YOUR_RAPIDAPI_KEY":
    print("⚠️ API key not set! Please create a config_local.py file with your RAPIDAPI_KEY")
    print("You can copy config_local.py.template to config_local.py and add your key there")
    sys.exit(1)

SAVE_FILE = "checked_domains.json"

KEYWORDS = [
    "pay", "bank", "fin", "money", "fund", "invest", "loan",
    "trade", "credit", "debt", "equity", "capital", "cash",
    "coin", "crypto", "ledger", "safe", "secure", "trust",
    "wealth", "market", "bond", "stock", "gold", "dollar"
]
TLDS = ["com", "net", "org", "ng", "io", "co", "finance", "money", "fund"]

BATCH_SIZE = 5  # check 5 domains per API call
DELAY = 1.0     # wait 1s between batches to avoid 429

def build_domains():
    domains = []
    for word in KEYWORDS:
        for tld in TLDS:
            domains.append(f"blooket{word}.{tld}")
    return domains

async def check_domains_batch(session, domains):
    url = f"https://{config.API_HOST}/v2/status"
    params = [("domain", d) for d in domains]

    headers = {
        "X-RapidAPI-Key": config.RAPIDAPI_KEY,
        "X-RapidAPI-Host": config.API_HOST,
    }

    try:
        # Create secure SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        async with session.get(url, headers=headers, params=params, ssl=ssl_context) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = {}
                for s in data.get("status", []):
                    results[s["domain"]] = s["status"]
                return results
            else:
                return {d: f"HTTP {resp.status}" for d in domains}
    except Exception as e:
        return {d: f"Error: {e}" for d in domains}

async def main():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            checked = json.load(f)
    else:
        checked = {}

    domains = build_domains()
    new_domains = [d for d in domains if d not in checked]

    print(f"🔎 Checking {len(new_domains)} new domains (batches of {BATCH_SIZE})...")

    async with aiohttp.ClientSession() as session:
        for i in range(0, len(new_domains), BATCH_SIZE):
            batch = new_domains[i:i + BATCH_SIZE]
            results = await check_domains_batch(session, batch)
            for domain, status in results.items():
                checked[domain] = status
                print(f"{domain}: {status}")

            with open(SAVE_FILE, "w") as f:
                json.dump(checked, f, indent=2)

            await asyncio.sleep(DELAY)  # prevent hitting 429

    print("✅ Scan completed and saved.")

if __name__ == "__main__":
    asyncio.run(main())
