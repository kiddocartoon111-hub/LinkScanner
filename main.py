import requests
import os
import csv
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

# --- CHECK 1: MANUAL/LOCAL CHECK (Free) ---
def first_check(url):
    try:
        # User-Agent add kiya taaki basic bot detection bypass ho sake
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        # Agar status 200 hai, toh link sahi hai
        if res.status_code == 200:
            return True, "OK"
        return False, f"Status {res.status_code}"
    except Exception as e:
        return False, str(e)

# --- CHECK 2: SCRAPER API CHECK (Paid/Deep Scan) ---
def deep_scan(url):
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true"
    broken_indicators = ["page not found", "404 error", "sorry, this page isn't available", "currently unavailable"]
    
    try:
        res = requests.get(proxy_url, timeout=45)
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
# (Yahan Sheet download wala code rahega...)
# Maan lete hain data list mein hai

for row in data:
    name, link = row['Name'], row['Link'].strip()
    
    # 1st STEP: Manual Check
    print(f"🔍 Normal Check: {name}...")
    is_ok, reason = first_check(link)
    
    if not is_ok:
        print(f"⚠️ Normal check failed ({reason}). Starting Deep Scan...")
        
        # 2nd STEP: Scraper API (Only if 1st fails)
        is_still_broken, final_reason = deep_scan(link)
        
        if not is_still_broken:
            print(f"❗ ALERT: Confirming Broken Link for {name}")
            send_telegram(f"🚨 *LINK BROKEN*\n*User:* {name}\n*Link:* {link}\n*Reason:* {final_reason}")
        else:
            print(f"✅ Deep Scan passed. Link is actually fine.")
    else:
        print(f"✅ {name} is Active.")

print("✅ All tasks finished!")
