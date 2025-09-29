import aiohttp
import asyncio
import csv
import os
import json
import ssl
import certifi
from wordfreq import top_n_list
import sys

# ===== CONFIG =====
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

HEADERS = {
    "x-rapidapi-key": config.RAPIDAPI_KEY,
    "x-rapidapi-host": config.API_HOST
}

# File paths
CSV_FILE = "checked_domains.csv"
AVAILABLE_FILE = "available_domains.csv"
API_USAGE_FILE = "api_usage.json"
CONCURRENCY = 10  # parallel requests

# ===== BUILT-IN STOPWORDS =====
STOPWORDS = {
    "a","about","above","after","again","against","all","am","an","and","any","are",
    "as","at","be","because","been","before","being","below","between","both","but",
    "by","could","did","do","does","doing","down","during","each","few","for","from",
    "further","had","has","have","having","he","her","here","hers","herself","him",
    "himself","his","how","i","if","in","into","is","it","its","itself","just","me",
    "more","most","my","myself","no","nor","not","now","of","off","on","once","only",
    "or","other","our","ours","ourselves","out","over","own","same","she","should",
    "so","some","such","than","that","the","their","theirs","them","themselves",
    "then","there","these","they","this","those","through","to","too","under","until",
    "up","very","was","we","were","what","when","where","which","while","who","whom",
    "why","with","would","you","your","yours","yourself","yourselves"
}

# ===== FINANCE WORDS =====
FINANCE_WORDS = [
    "invest","pay","loan","fund","trade","cash","bank","market","save",
    "credit","coin","buy","sell","profit","wallet","finance","money",
    "deal","capital","wealth","funding","equity","asset","loaner","funds"
]

# ===== PREFIXES & SUFFIXES =====
PREFIXES = ["my","get","pro","fin","smart","easy"]
SUFFIXES = ["hub","wallet","fund","capital","bank","trade"]

# ===== HELPERS =====
def is_marketable(word):
    """Return True if the word is alphabetic, 3-12 letters, and not a stopword."""
    return word.isalpha() and 3 <= len(word) <= MAX_WORD_LENGTH and word.lower() not in STOPWORDS

def parse_status(status_str):
    flags = status_str.split()
    main_flag = flags[-1] if flags else "unknown"
    if main_flag == "inactive":
        return "available"
    elif main_flag in ["premium","priced","marketed","transferable"]:
        return "premium"
    else:
        return "taken"

# ===== BUILD WORDLIST =====
def build_wordlist():
    english_words = [w.lower() for w in top_n_list("en", TOP_ENGLISH_WORDS) if is_marketable(w)]
    finance_english = [w for w in english_words if w in FINANCE_WORDS]
    seeds = [w for w in FINANCE_WORDS if is_marketable(w)]
    combined = sorted(set(finance_english + seeds), key=lambda w: (len(w), w))
    return combined

def expand_finance_domains(words):
    expanded = set()
    for w in words:
        expanded.add(w)
        for p in PREFIXES:
            merged = p + w
            if len(merged) <= MAX_WORD_LENGTH:
                expanded.add(merged)
        for s in SUFFIXES:
            merged = w + s
            if len(merged) <= MAX_WORD_LENGTH:
                expanded.add(merged)
    return list(expanded)

# ===== CSV LOGGING =====
def load_checked():
    checked = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE,"r") as f:
            reader = csv.reader(f)
            next(reader,None)
            for row in reader:
                if row:
                    checked.add(row[0])
    return checked

def save_result(domain,state):
    exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE,"a",newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["Domain","Status"])
        writer.writerow([domain,state])

def save_available(domain,state):
    exists = os.path.exists(AVAILABLE_FILE)
    with open(AVAILABLE_FILE,"a",newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["Domain","Status"])
        writer.writerow([domain,state])

# ===== API USAGE =====
def load_api_usage():
    if os.path.exists(API_USAGE_FILE):
        with open(API_USAGE_FILE,"r") as f:
            data = json.load(f)
            return data.get("calls",0)
    return 0

def save_api_usage(calls):
    with open(API_USAGE_FILE,"w") as f:
        json.dump({"calls": calls}, f)

# ===== ASYNC DOMAIN CHECK =====
async def check_domain(session, word, semaphore):
    domain = f"{word}.{config.DEFAULT_TLD}"
    async with semaphore:
        try:
            url = f"https://domainr.p.rapidapi.com/v2/status?domain={domain}"
            async with session.get(url, headers=HEADERS, timeout=10) as r:
                data = await r.json()
                status_str = data["status"][0]["status"]
                availability = parse_status(status_str)
                return domain, availability
        except Exception as e:
            return domain, f"error:{e}"

# ===== MAIN ASYNC =====
async def main():
    print("🔎 Building finance-focused wordlist...")
    words = expand_finance_domains(build_wordlist())
    print(f"✅ Wordlist built with {len(words)} finance-related words")

    checked = load_checked()
    print(f"📂 Loaded {len(checked)} already checked domains")

    api_calls = load_api_usage()
    print(f"📈 API calls used so far: {api_calls}/{API_CALL_LIMIT}")

    semaphore = asyncio.Semaphore(CONCURRENCY)
    # Create SSL context with secure protocol
    sslcontext = ssl.create_default_context(cafile=certifi.where())
    # Set minimum TLS version to 1.2 for better security
    sslcontext.minimum_version = ssl.TLSVersion.TLSv1_2

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=sslcontext)) as session:
        for i in range(0, len(words), CONCURRENCY):
            batch = words[i:i+CONCURRENCY]
            batch = [w for w in batch if f"{w}.ng" not in checked]
            if not batch:
                continue

            tasks = [check_domain(session, w, semaphore) for w in batch]

            for future in asyncio.as_completed(tasks):
                domain,state = await future
                if api_calls >= API_CALL_LIMIT:
                    print(f"⚠️ API call limit reached ({API_CALL_LIMIT}). Stopping script.")
                    return
                api_calls += 1
                save_api_usage(api_calls)

                if state.startswith("error"):
                    print(f"⚠️ Skipped {domain}: {state}")
                    continue

                save_result(domain,state)
                checked.add(domain)

                if state in ["available","premium"]:
                    save_available(domain,state)

                if state=="available":
                    print(f"✅ Available: {domain}")
                elif state=="premium":
                    print(f"💰 Premium: {domain}")
                else:
                    print(f"❌ Taken: {domain}")

    print("\n🎉 Done! Results saved to CSV files")
    print(f"📈 Total API calls used: {api_calls}/{API_CALL_LIMIT}")

if __name__=="__main__":
    asyncio.run(main())
