import os
import asyncio
import random
import threading
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID", 36062585))
API_HASH = os.getenv("API_HASH", "27af3370413767173feb169bec5065f9")
SESSION_STRING = os.getenv("SESSION_STRING") 
# IMPORTANT: Put the @username of the bot you want to message here
TARGET_BOT = "@TheUsernameOfYourBot" 

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is active and running!"

def run_flask():
    # Render uses port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def auto_grow():
    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        print("Logged in successfully!")
        while True:
            try:
                await client.send_message(TARGET_BOT, "/grow")
                print(f"Sent /grow to {TARGET_BOT}")
            except Exception as e:
                print(f"Error sending message: {e}")

            # Wait 30 seconds + 1-5 random seconds for safety
            wait_time = 30 + random.randint(1, 5)
            print(f"Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)

if __name__ == "__main__":
    # Start the web server in the background
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start the Telegram automation
    asyncio.run(auto_grow())
