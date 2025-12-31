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

app = Flask(__name__)

# Helper to get PH time easily
def get_ph_time():
    return datetime.now(timezone(timedelta(hours=8)))

@app.route('/')
def home():
    ph_now = get_ph_time()
    ph_hour = ph_now.hour
    
    # Logic to determine status for the web page
    if 7 <= ph_hour < 23:
        status = "🟢 AWAKE (Farming Points)"
    else:
        status = "🔴 SLEEPING (Stealth Night Mode)"
        
    return f"""
    <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h1>Bot Status: {status}</h1>
            <p>Current Philippines Time: <b>{ph_now.strftime('%I:%M %p')}</b></p>
            <p>Farming Hours: 07:00 AM - 11:00 PM</p>
            <hr width="300">
            <p><small>Check Render Logs for detailed activity.</small></p>
        </body>
    </html>
    """

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def auto_grow():
    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        print("Bot started and connected to Telegram.")
        
        while True:
            ph_now = get_ph_time()
            ph_hour = ph_now.hour

            # Check if it's "Active Hours" (7 AM to 11 PM Manila Time)
            if 7 <= ph_hour < 23:
                try:
                    # Simulate human typing
                    async with client.action(TARGET_BOT, 'typing'):
                        await asyncio.sleep(random.uniform(2, 5))
                        await client.send_message(TARGET_BOT, "/grow")
                        print(f"[{ph_now.strftime('%I:%M %p')}] Sent /grow")
                except Exception as e:
                    print(f"Error: {e}")
                
                # Wait 45-90 seconds + random break chance
                wait_time = random.randint(45, 90)
                if random.random() < 0.05: # 5% chance of a longer break
                    wait_time = random.randint(300, 600)
                    print("Taking a 5-10 minute break...")
                    
                await asyncio.sleep(wait_time)
            else:
                # Night Mode
                print(f"[{ph_now.strftime('%I:%M %p')}] PH Night Mode: Sleeping...")
                await asyncio.sleep(900) # Check every 15 mins during night

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(auto_grow())
