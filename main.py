import os
import asyncio
import random
import threading
from datetime import datetime, timedelta, timezone
from flask import Flask
from telethon import TelegramClient, events, errors
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
last_bot_reply = "Waiting for your first grow..."
bot_log = []
total_grows_today = 0
is_blocked = False 

app = Flask(__name__)

def get_ph_time():
    return datetime.now(timezone(timedelta(hours=8)))

@app.route('/')
def home():
    ph_now = get_ph_time()
    is_night = not (7 <= ph_now.hour < 23)
    
    if is_night:
        status_text, status_color = "🔴 SLEEPING", "#ff4d4d"
    elif is_blocked:
        status_text, status_color = "⚠️ MUTED/REMOVED", "#fbbf24"
    else:
        status_text, status_color = "🟢 ACTIVE", "#2ecc71"
    
    countdown_text = "Resumes at 07:00 AM"
    if not is_night:
        if is_blocked:
            countdown_text = "Retrying in 5 mins..."
        elif next_run_time:
            diff = int((next_run_time - ph_now).total_seconds())
            countdown_text = f"Next Grow in: {diff}s" if diff > 0 else "Processing..."

    log_html = "".join([f"<div style='border-bottom:1px solid #333; padding:4px 0;'>{l}</div>" for l in bot_log[-10:]])

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PH Grow Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #0f172a; color: white; margin: 0; padding: 15px; text-align: center; }}
            .card {{ background: #1e293b; max-width: 500px; margin: auto; padding: 20px; border-radius: 20px; border: 1px solid #334155; }}
            .timer {{ font-size: 2em; font-weight: bold; margin: 15px 0; color: #38bdf8; }}
            .reply-box {{ background: #0f172a; padding: 15px; border-radius: 12px; text-align: left; border-left: 4px solid #38bdf8; white-space: pre-wrap; font-size: 0.95em; }}
            .stat-box {{ background: #334155; padding: 15px; border-radius: 12px; margin: 20px 0; }}
            .log {{ background: #000; color: #4ade80; font-family: monospace; padding: 10px; border-radius: 10px; font-size: 0.75em; text-align: left; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div style="color: {status_color}; font-weight: bold;">{status_text}</div>
            <div class="timer">{countdown_text}</div>
            <div class="stat-box">
                <small style="color:#94a3b8;">GROWS TODAY</small><br>
                <b style="font-size:2em;">{total_grows_today}</b>
            </div>
            <div style="text-align:left; color:#94a3b8; font-size:0.8em; margin-bottom: 5px;">LATEST GROWTH INFO:</div>
            <div class="reply-box">{last_bot_reply}</div>
            <div class="log">{log_html if log_html else "Initializing..."}</div>
        </div>
    </body>
    </html>
    """

async def main_logic():
    global last_sent_time, next_run_time, last_bot_reply, bot_log, total_grows_today, is_blocked
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    @client.on(events.NewMessage(chats=GROUP_TARGET, from_users=BOT_USERNAME))
    async def handler(event):
        global last_bot_reply
        if MY_USERNAME.lower() in event.text.lower() and "BATTLE RESULT" not in event.text.upper():
            last_bot_reply = event.text
            await asyncio.sleep(random.uniform(2, 4))
            await client.send_read_acknowledge(event.chat_id, event.message)

    async with client:
        while True:
            ph_now = get_ph_time()
            if 7 <= ph_now.hour < 23:
                try:
                    async with client.action(GROUP_TARGET, 'typing'):
                        await asyncio.sleep(random.uniform(4, 7))
                        await client.send_message(GROUP_TARGET, "/grow")
                        
                        is_blocked = False 
                        total_grows_today += 1
                        last_sent_time = ph_now
                        bot_log.append(f"[{ph_now.strftime('%H:%M')}] Sent /grow")

                except (errors.ChatWriteForbiddenError, errors.ChatAdminRequiredError):
                    if not is_blocked: # Only send panic message once
                        await client.send_message("me", f"⚠️ **GROW BOT ALERT**\n\nThe group chat ({GROUP_TARGET}) has been muted or you have been removed. Retrying every 5 minutes.")
                    is_blocked = True
                    bot_log.append(f"[{ph_now.strftime('%H:%M')}] ⚠️ MUTED: Sent alert to Saved Messages.")
                    await asyncio.sleep(300) 
                    continue
                except Exception as e:
                    bot_log.append(f"Error: {str(e)[:20]}")
                    await asyncio.sleep(60)

                wait_seconds = random.randint(45, 90)
                next_run_time = get_ph_time() + timedelta(seconds=wait_seconds)
                await asyncio.sleep(wait_seconds)
            else:
                next_run_time = None
                await asyncio.sleep(600)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_logic())
