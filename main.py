import os
import asyncio
import random
import threading
from datetime import datetime, timedelta, timezone
from flask import Flask
from telethon import TelegramClient, events, errors, functions
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID", 36062585))
API_HASH = os.getenv("API_HASH", "27af3370413767173feb169bec5065f9")
SESSION_STRING = os.getenv("SESSION_STRING") 

GROUP_TARGET = -1003598172312 
MY_USERNAME = "AryaCollymore"   
BOT_USERNAME = "FkerKeyBot"

# --- GLOBAL TRACKING ---
last_sent_time = None
next_run_time = None
last_bot_reply = "System active 24/7. Monitoring group..."
bot_log = []
total_grows_today = 0
is_blocked = False 

app = Flask(__name__)

def get_ph_time():
    return datetime.now(timezone(timedelta(hours=8)))

@app.route('/')
def home():
    ph_now = get_ph_time()
    
    # Status Logic (Sleep removed)
    if is_blocked:
        status_text, status_color = "⚠️ MUTED/REMOVED", "#fbbf24"
    else:
        status_text, status_color = "🟢 ACTIVE 24/7", "#2ecc71"
    
    countdown_text = "Processing..."
    if is_blocked:
        countdown_text = "Retrying in 5 mins..."
    elif next_run_time:
        diff = int((next_run_time - ph_now).total_seconds())
        countdown_text = f"Next Grow in: {diff}s" if diff > 0 else "Sending command..."

    log_html = "".join([f"<div style='border-bottom:1px solid #333; padding:4px 0;'>{l}</div>" for l in bot_log[-10:]])

    return f"""
    <html>
    <head>
        <title>PH 24/7 Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ font-family: sans-serif; background: #0f172a; color: white; text-align: center; padding: 15px; }}
            .card {{ background: #1e293b; max-width: 500px; margin: auto; padding: 20px; border-radius: 20px; border: 1px solid #334155; }}
            .timer {{ font-size: 2em; font-weight: bold; margin: 15px 0; color: #38bdf8; }}
            .reply-box {{ background: #0f172a; padding: 15px; border-radius: 12px; text-align: left; border-left: 4px solid #38bdf8; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div style="color: {status_color}; font-weight: bold;">{status_text}</div>
            <div class="timer">{countdown_text}</div>
            <h2 style="margin: 0;">Grows: {total_grows_today}</h2>
            <hr style="border: 0.1px solid #334155; margin: 20px 0;">
            <div style="text-align:left; font-size:0.8em; color:#94a3b8;">LATEST BOT REPLY:</div>
            <div class="reply-box">{last_bot_reply}</div>
        </div>
    </body>
    </html>
    """

async def main_logic():
    global last_sent_time, next_run_time, last_bot_reply, bot_log, total_grows_today, is_blocked
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    # CLEAR NOTIFICATIONS: Instantly removes the "@" mention and marks group as read
    @client.on(events.NewMessage(chats=GROUP_TARGET))
    async def handler(event):
        global last_bot_reply
        try:
            await client(functions.messages.ReadMentionsRequest(peer=GROUP_TARGET))
            await client.send_read_acknowledge(event.chat_id, event.message)
        except:
            pass

        if event.sender_id and str(event.sender.username).lower() == BOT_USERNAME.strip('@').lower():
            if MY_USERNAME.lower() in event.text.lower() and "BATTLE RESULT" not in event.text.upper():
                last_bot_reply = event.text

    async with client:
        bot_log.append("[SYSTEM] 24/7 Mode Engaged.")
        while True:
            ph_now = get_ph_time()
            try:
                # 1. Human Mimicry
                async with client.action(GROUP_TARGET, 'typing'):
                    await asyncio.sleep(random.uniform(4, 7))
                    
                    # 2. Command
                    await client.send_message(GROUP_TARGET, "/grow")
                    
                    is_blocked = False 
                    total_grows_today += 1
                    last_sent_time = ph_now
                    bot_log.append(f"[{ph_now.strftime('%H:%M')}] Grow Success")

            except (errors.ChatWriteForbiddenError, errors.ChatAdminRequiredError):
                if not is_blocked:
                    await client.send_message("me", "⚠️ Bot Muted by Admin. Will retry every 5m.")
                is_blocked = True
                await asyncio.sleep(300) 
                continue
            except Exception as e:
                bot_log.append(f"Error: {str(e)[:20]}")
                await asyncio.sleep(60)

            # 3. Random Interval (stays safe while working fast)
            wait_seconds = random.randint(45, 90)
            next_run_time = get_ph_time() + timedelta(seconds=wait_seconds)
            await asyncio.sleep(wait_seconds)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_logic())
