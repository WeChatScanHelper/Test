import os
import asyncio
import random
import threading
from datetime import datetime, timedelta, timezone
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID", 36062585))
API_HASH = os.getenv("API_HASH", "27af3370413767173feb169bec5065f9")
SESSION_STRING = os.getenv("SESSION_STRING") 
TARGET_BOT = "@FkerKeyBot" 

# --- GLOBAL TRACKING ---
last_sent_time = None
bot_log = []

app = Flask(__name__)

def get_ph_time():
    return datetime.now(timezone(timedelta(hours=8)))

@app.route('/')
def home():
    ph_now = get_ph_time()
    ph_hour = ph_now.hour
    
    # 1. Determine Status
    if 7 <= ph_hour < 23:
        status = "<span style='color: green;'>🟢 AWAKE</span>"
    else:
        status = "<span style='color: red;'>🔴 SLEEPING (Stealth Mode)</span>"
    
    # 2. Calculate "Time Since Last Message"
    time_info = "Waiting for first message..."
    if last_sent_time:
        diff = ph_now - last_sent_time
        seconds = int(diff.total_seconds())
        if seconds < 60:
            time_info = f"{seconds} seconds ago"
        else:
            time_info = f"{seconds // 60} minutes ago"

    # 3. Create Log View
    recent_logs = "".join([f"<li>{l}</li>" for l in bot_log[-5:]]) # Show last 5 logs

    return f"""
    <html>
        <body style="font-family: sans-serif; text-align: center; padding: 20px; background-color: #f4f4f9;">
            <div style="background: white; display: inline-block; padding: 30px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h1>Bot Dashboard</h1>
                <h3>Status: {status}</h3>
                <p><b>Current PH Time:</b> {ph_now.strftime('%I:%M:%p')}</p>
                <p><b>Last /grow sent:</b> <span style="color: blue;">{time_info}</span></p>
                <hr>
                <div style="text-align: left; background: #eee; padding: 10px; border-radius: 5px;">
                    <p style="margin-top: 0;"><b>Recent Activity:</b></p>
                    <ul style="font-size: 0.9em; padding-left: 20px;">{recent_logs if recent_logs else "No activity yet..."}</ul>
                </div>
            </div>
        </body>
    </html>
    """

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def auto_grow():
    global last_sent_time, bot_log
    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        print("Bot started.")
        
        while True:
            ph_now = get_ph_time()
            ph_hour = ph_now.hour

            if 7 <= ph_hour < 23:
                try:
                    async with client.action(TARGET_BOT, 'typing'):
                        await asyncio.sleep(random.uniform(2, 5))
                        await client.send_message(TARGET_BOT, "/grow")
                        
                        # Update global variables for the website
                        last_sent_time = ph_now
                        bot_log.append(f"Sent /grow at {ph_now.strftime('%I:%M:%S %p')}")
                        if len(bot_log) > 10: bot_log.pop(0) # Keep log short

                except Exception as e:
                    bot_log.append(f"Error: {str(e)[:50]}")
                
                wait_time = random.randint(45, 90)
                await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(600) # Check every 10 mins during night

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(auto_grow())
