import requests
import os
from datetime import datetime, timedelta

# --- SETTINGS (GitHub Secrets se automatic aayega) ---
SCRAPER_API_KEY = os.environ.get('SCRAPER_KEY')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# --- DATABASE (Influencers ki list) ---
# join_date format: YYYY-MM-DD (Saal-Mahina-Din)
database = [
    {"name": "Rohit_Tech", "link": "https://blueroseone.com/publish/wordsbrew/", "join_date": "2026-01-20", "plan": "Free"},
    {"name": "Sneha_Vlogs", "link": "https://www.amazon.in/dp/B0CHX1W1XY", "join_date": "2026-01-15", "plan": "Paid"},
    {"name": "Testing_User", "link": "https://www.amazon.in/dp/B0CHX_FAKE_LINK_123", "join_date": "2026-01-23", "plan": "Free"}
]

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def check_link(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    # Stage 1: Normal Scan
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200: return "✅ ACTIVE"
    except: pass
    
    # Stage 2: Deep Scan (ScraperAPI)
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    try:
        res = requests.get(proxy_url, timeout=30)
        if res.status_code == 200:
            if "Currently unavailable" in res.text or "Out of Stock" in res.text:
                return "⚠️ OUT OF STOCK"
            return "✅ ACTIVE (Deep Scan)"
        return f"❌ BROKEN ({res.status_code})"
    except: return "🚨 DOWN"

# --- RUNNER ---
today = datetime.now()
print(f"Starting Scan: {today.strftime('%Y-%m-%d %H:%M')}")

for user in database:
    # 1. Expiry Check Logic
    join_dt = datetime.strptime(user['join_date'], "%Y-%m-%d")
    days_limit = 7 if user['plan'] == "Free" else 30
    expiry_dt = join_dt + timedelta(days=days_limit)
    days_left = (expiry_dt - today).days

    # Alert if Plan Expired or Expiring soon
    if days_left == 0:
        send_telegram_alert(f"⏰ *PLAN EXPIRING TODAY*\nUser: {user['name']}\nPlan: {user['plan']}\nBhai, isse payment mang lo!")
    elif days_left < 0:
        print(f"Skipping {user['name']} - Plan Expired.")
        continue 

    # 2. Link Status Check
    status = check_link(user['link'])
    print(f"Result for {user['name']}: {status}")

    if "✅" not in status:
        alert_msg = f"❗ *LINK ISSUE DETECTED*\n\n*User:* {user['name']}\n*Status:* {status}\n*Link:* {user['link']}\n\n_Check karke influencer ko update karo!_"
        send_telegram_alert(alert_msg)
