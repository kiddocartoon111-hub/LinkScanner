import requests
import os
import csv
from datetime import datetime, timedelta

# --- SETTINGS FROM GITHUB SECRETS ---
SHEET_URL = os.environ.get('SHEET_URL')
SCRAPER_API_KEY = os.environ.get('SCRAPER_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_sheet_data():
    try:
        response = requests.get(SHEET_URL)
        response.raise_for_status()
        decoded_content = response.content.decode('utf-8')
        cr = csv.DictReader(decoded_content.splitlines(), delimiter=',')
        return list(cr)
    except Exception as e:
        print(f"Sheet Download Error: {e}")
        return []

def check_link(url):
    # Amazon bypass using ScraperAPI
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    try:
        res = requests.get(proxy_url, timeout=30)
        if res.status_code == 200:
            if "Currently unavailable" in res.text or "kuch_aur_error_text" in res.text:
                return "🚨 OUT OF STOCK"
            return "✅ ACTIVE"
        return f"❌ BROKEN (Status: {res.status_code})"
    except:
        return "🚨 SERVER DOWN"

# --- MAIN ENGINE ---
print("Starting Link Scanner...")
data = get_sheet_data()
today = datetime.now()

for row in data:
    name = row.get('Name')
    link = row.get('Link')
    plan = row.get('Plan')
    join_date_str = row.get('Join_Date')

    if not name or not link: continue

    # Expiry Logic
    join_dt = datetime.strptime(join_date_str, "%Y-%m-%d")
    limit = 7 if plan.lower() == "free" else 30
    expiry_dt = join_dt + timedelta(days=limit)

    if today > expiry_dt:
        print(f"Skipping {name}: Plan Expired")
        send_telegram(f"🚫 *SCAN STOPPED*\n\n*User:* {name}\n*Reason:* Plan Expired ({plan})\n*Action:* Please renew payment to resume scanning.")
        continue

    # Plan active hai, toh scan karo
    print(f"Scanning {name}...")
    status = check_link(link)
    
    if "✅" not in status:
        send_telegram(f"❗ *LINK ISSUE DETECTED*\n\n*User:* {name}\n*Status:* {status}\n*Link:* {link}")

print("Scan Task Completed!")
