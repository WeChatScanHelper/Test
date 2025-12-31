
import os
import asyncio
import random
import threading
from datetime import datetime
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID", 36062585))
API_HASH = os.getenv("API_HASH", "27af3370413767173feb169bec5065f9")
SESSION_STRING = os.getenv("SESSION_STRING") 
TARGET_BOT = "@FkerKeyBot" 

# --- PHILIPPINES STEALTH SETTINGS (UTC+8) ---
# 11:00 PM PHT is 15:00 UTC
# 06:00 AM PHT is 22:00 UTC
SLEEP_START_UTC = 15 
SLEEP_END_UTC = 22

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running in Stealth Mode (PH Timezone Optimized)."

def run_flask():
    # Use Render's dynamic port
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def auto_grow():
    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        print("Successfully connected. Human simulation active.")
        
        while True:
            # Get current hour in UTC
            now_utc = datetime.utcnow().hour
            
            # 1. NIGHT MODE: The bot 'sleeps' when you sleep in PH
            if SLEEP_START_UTC <= now_utc or now_utc < (SLEEP_END_UTC - 24 if SLEEP_END_UTC > 24 else SLEEP_END_UTC):
                print(f"[{datetime.now().strftime('%I:%M %p')}] PH Night Mode: Sleeping for 30 mins...")
                await asyncio.sleep(1800) 
                continue

            try:
                # 2. SIMULATE TYING: Shows "User is typing..." in the chat
                async with client.action(TARGET_BOT, 'typing'):
                    # Wait 2-5 seconds while "typing" to look natural
                    await asyncio.sleep(random.uniform(2.5, 5.2))
                    
                    await client.send_message(TARGET_BOT, "/grow")
                    print(f"[{datetime.now().strftime('%I:%M %p')}] Command sent: /grow")

            except Exception as e:
                print(f"Error encountered: {e}")
                # Wait 5 minutes if there's a connection issue
                await asyncio.sleep(300)

            # 3. RANDOMIZED INTERVALS (The "Jitter")
            # Instead of exactly 30s, we wait 45 to 90 seconds randomly
            wait_time = random.randint(45, 90)
            
            # 4. RANDOM BREAKS: 10% chance to take a 5-10 minute break
            if random.random() < 0.10:
                wait_time = random.randint(300, 600)
                print("Taking a quick coffee break (Simulated Human behavior)...")

            print(f"Waiting {wait_time}s for next action.")
            await asyncio.sleep(wait_time)

if __name__ == "__main__":
    # Start web server so Render doesn't shut us down
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start the bot loop
    asyncio.run(auto_grow())
