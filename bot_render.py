import feedparser
import requests
import time
import schedule
import logging
import re
import threading
from flask import Flask
from datetime import datetime
from deep_translator import GoogleTranslator

# --- إعدادات Flask لضمان استمرارية الخدمة على Render ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- إعدادات البوت ---
TOKEN = "8665699009:AAFodvJuv5aw6yifWs1I7EBd5ZXhiF4VOHI"
CHAT_ID = "1934770017"

RSS_FEEDS = [
    "https://www.wired.com/feed/category/ideas/latest/rss",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.artificialintelligence-news.com/feed/",
    "https://theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://openai.com/news/rss.xml"
]

sent_articles = set()

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def translate_text(text, target_lang='ar'):
    try:
        if not text: return ""
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return text

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=20)
    except Exception as e:
        logging.error(f"Telegram error: {e}")

def fetch_and_send_news():
    logging.info("Checking for news...")
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                if entry.link not in sent_articles:
                    title_ar = translate_text(entry.title)
                    summary_en = re.sub('<[^<]+?>', '', entry.get('summary', entry.get('description', '')))[:200]
                    summary_ar = translate_text(summary_en)
                    
                    message = (
                        f"🆕 *خبر جديد في الذكاء الاصطناعي*\n\n"
                        f"📌 *{title_ar}*\n\n"
                        f"📝 {summary_ar}...\n\n"
                        f"🔗 [المصدر الأصلي]({entry.link})"
                    )
                    send_telegram_message(message)
                    sent_articles.add(entry.link)
                    time.sleep(2)
        except Exception as e:
            logging.error(f"Error: {e}")

def run_scheduler():
    fetch_and_send_news() # أول تشغيل
    schedule.every(15).minutes.do(fetch_and_send_news)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # تشغيل Flask في خيط (Thread) منفصل
    t = threading.Thread(target=run_flask)
    t.start()
    
    # تشغيل البوت والجدولة
    run_scheduler()
