import requests
import os
import csv
import time
from datetime import datetime, timedelta

# --- SETTINGS ---
SHEET_URL = os.environ.get('SHEET_URL')
SCRAPER_API_KEY = os.environ.get('SCRAPER_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def first_check(url):
    """Pahla check: Normal Request"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if res.status_code == 200:
            return True, "OK"
        return False, f"Status {res.status_code}"
    except Exception as e:
        return False, "Connection Error"

def deep_scan(url):
    """Doosra check: Scraper API (JS Rendering)"""
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true&premium=true"
    broken_indicators = ["page not found", "404 error", "sorry, this page isn't available", "currently unavailable", "link expired"]
    
    try:
        res = requests.get(proxy_url, timeout=60)
        if res.status_code == 200:
            content_lower = res.text.lower()
            for word in broken_indicators:
                if word in content_lower:
                    return False, f"Broken Content ({word})"
            return True, "Active"
        return False, f"API Status {res.status_code}"
    except:
        return False, "API Timeout"

# --- MAIN ENGINE ---
print("🚀 Launching Smart Link Scanner...")

# 1. Google Sheet Data Download
data = []
try:
    response = requests.get(SHEET_URL)
    response.raise_for_status()
    decoded_content = response.content.decode('utf-8')
    cr = csv.DictReader(decoded_content.splitlines(), delimiter=',')
    data = list(cr)
    print(f"✅ Loaded {len(data)} links from sheet.")
except Exception as e:
    print(f"❌ Sheet Download Error: {e}")
    send_telegram(f"🚨 *CRITICAL ERROR*: Google Sheet download nahi ho rahi!")

# 2. Processing Links
today = datetime.now()

for row in data:
    name = row.get('Name', 'Unknown')
    link = row.get('Link', '').strip()
    plan = row.get('Plan', 'Free').strip().lower()
    join_date_str = row.get('Join_Date', '').strip()

    if not link or not join_date_str:
        continue

    # --- Subscription Logic ---
    try:
        join_dt = datetime.strptime(join_date_str, "%Y-%m-%d")
        plan_days = {"early": 365, "paid": 30, "free": 7}
        limit_days = plan_days.get(plan, 7)
        expiry_dt = join_dt + timedelta(days=limit_days)
    except:
        continue

    if today > expiry_dt:
        print(f"🚫 Plan Expired for {name}")
        continue

    # --- Scanning Process ---
    print(f"🔍 Checking: {name}...")
    
    # Step 1: Normal Check
    is_ok, reason = first_check(link)
    
    if not is_ok:
        print(f"⚠️ Normal check failed ({reason}). Starting Deep Scan via ScraperAPI...")
        
        # Step 2: Deep Scan (Only if Step 1 fails)
        is_still_ok, final_reason = deep_scan(link)
        
        if not is_still_ok:
            print(f"❌ Link is BROKEN for {name}")
            send_telegram(f"🚨 *LINK ISSUE*: {name}\n🔗 *Link*: {link}\n📊 *Reason*: {final_reason}")
        else:
            print(f"✅ Deep Scan passed. Link is fine.")
    else:
        print(f"✅ {name} is Active.")

    time.sleep(1) # Chhota gap requests ke beech

print("✅ All tasks finished!")
