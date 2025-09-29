import aiohttp
import asyncio
import csv
import os
import json
import ssl
import certifi
from itertools import combinations, product

# ===== CONFIG =====
RAPIDAPI_KEY = "77499b45c4mshd7c1dd9843b1855p17f35bjsn7781c1a5e6df"
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "domainr.p.rapidapi.com"
}
CSV_FILE = "mom_domain.csv"
MAX_WORD_LENGTH = 15
TLDS = [".com", ".net", ".info", ".io", ".me"]
CONCURRENCY = 3  # reduce concurrency to avoid 429
RETRY_DELAY = 5  # seconds

# ===== MATERNITY KEYWORDS =====
MATERNITY_WORDS = [
    "mom","baby","bump","lullaby","newborn","nursery","pregnancy","crib","stroller",
    "maternity","breastfeed","diaper","toddler","infant","parent","parenting","babycare","momlife"
]

# ===== HELPERS =====
def is_marketable(word):
    """Filter words to reasonable length and alphabetic only"""
    return word.isalpha() and 2 <= len(word) <= MAX_WORD_LENGTH

def parse_status(status_str):
    flags = status_str.split()
    main_flag = flags[-1] if flags else "unknown"
    if main_flag == "inactive":
        return "available"
    else:
        return "taken"

# ===== CSV LOGGING =====
def save_available(domain):
    exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE,"a",newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["Domain"])
        writer.writerow([domain])

# ===== ASYNC DOMAIN CHECK =====
async def check_domain(session, domain):
    url = f"https://domainr.p.rapidapi.com/v2/status?domain={domain}"
    try:
        async with session.get(url, headers=HEADERS, timeout=15) as r:
            if r.status == 429:
                return "rate_limit"
            data = await r.json()
            status_str = data["status"][0]["status"]
            return parse_status(status_str)
    except Exception as e:
        return f"error:{e}"

# ===== MAIN ASYNC =====
async def main():
    print(f"🔎 Generating domains for maternity niche...")

    # Generate single and compound names
    words = [w for w in MATERNITY_WORDS if is_marketable(w)]
    combined_names = set(words)
    
    # Combine two words for more domain ideas
    for w1, w2 in combinations(words, 2):
        combined_names.add(w1 + w2)
        combined_names.add(w2 + w1)

    # Prepare full domain list
    domain_list = [name + tld for name, tld in product(combined_names, TLDS)]
    print(f"✅ Total domains to check: {len(domain_list)}")

    sslcontext = ssl.create_default_context(cafile=certifi.where())
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=sslcontext)) as session:
        for i in range(0, len(domain_list), CONCURRENCY):
            batch = domain_list[i:i+CONCURRENCY]
            tasks = []
            for domain in batch:
                tasks.append(check_domain_with_retry(session, semaphore, domain))

            results = await asyncio.gather(*tasks)
            for domain, status in results:
                if status == "available":
                    save_available(domain)
                    print(f"✅ Available: {domain}")
                elif status.startswith("error"):
                    print(f"⚠️ Error: {domain} -> {status}")
                else:
                    print(f"❌ Taken: {domain}")

async def check_domain_with_retry(session, semaphore, domain, retries=3):
    async with semaphore:
        for attempt in range(retries):
            status = await check_domain(session, domain)
            if status != "rate_limit":
                return domain, status
            print(f"⚠️ Rate limit hit for {domain}. Retrying in {RETRY_DELAY}s...")
            await asyncio.sleep(RETRY_DELAY)
        return domain, "rate_limit"

if __name__ == "__main__":
    asyncio.run(main())
