import os
import asyncio
import random
import threading
from datetime import datetime, timedelta, timezone
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID", 36062585))
API_HASH = os.getenv("API_HASH", "27af3370413767173feb169bec5065f9")
SESSION_STRING = os.getenv("SESSION_STRING") 
TARGET_BOT = "@FkerKeyBot" 

# --- GLOBAL TRACKING ---
last_sent_time = None
next_run_time = None
last_bot_reply = "Waiting for initial connection..."
bot_log = []
bot_status_msg = "Starting engine..."
total_grows_today = 0

app = Flask(__name__)

def get_ph_time():
    return datetime.now(timezone(timedelta(hours=8)))

@app.route('/')
def home():
    ph_now = get_ph_time()
    ph_hour = ph_now.hour
    
    # Status and Countdown Logic
    is_night = not (7 <= ph_hour < 23)
    status_color = "#ff4d4d" if is_night else "#2ecc71"
    status_text = "🔴 SLEEPING (Night Mode)" if is_night else "🟢 ACTIVE"
    
    countdown_text = "Resumes at 07:00 AM PHT"
    if not is_night:
        if next_run_time:
            diff = int((next_run_time - ph_now).total_seconds())
            countdown_text = f"Next Grow in: {diff}s" if diff > 0 else "Sending command..."
        else:
            countdown_text = "Initializing next cycle..."

    # Formatting Logs
    log_html = "".join([f"<div style='border-bottom:1px solid #333; padding:4px 0;'>{l}</div>" for l in bot_log[-10:]])

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PH Bot Ultimate</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #0f172a; color: white; margin: 0; padding: 15px; }}
            .container {{ max-width: 500px; margin: auto; }}
            .card {{ background: #1e293b; padding: 20px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }}
            .status-badge {{ display: inline-block; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8em; background: rgba(0,0,0,0.3); color: {status_color}; border: 1px solid {status_color}; }}
            .timer-box {{ font-size: 1.8em; font-weight: bold; margin: 20px 0; color: #38bdf8; text-shadow: 0 0 10px rgba(56, 189, 248, 0.3); }}
            .reply-box {{ background: #0f172a; padding: 15px; border-radius: 12px; text-align: left; font-size: 0.9em; border-left: 4px solid #38bdf8; white-space: pre-wrap; }}
            .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 20px 0; }}
            .stat-item {{ background: #334155; padding: 10px; border-radius: 10px; }}
            .log-area {{ background: #000; color: #4ade80; font-family: monospace; padding: 15px; border-radius: 10px; font-size: 0.75em; text-align: left; overflow: hidden; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h2 style="margin:0;">PH Ultimate</h2>
                    <div class="status-badge">{status_text}</div>
                </div>
                
                <div class="timer-box">{countdown_text}</div>

                <div class="stats-grid">
                    <div class="stat-item"><small style="color:#94a3b8;">Today's Count</small><br><span style="font-size:1.4em;">{total_grows_today}</span></div>
                    <div class="stat-item"><small style="color:#94a3b8;">Local Time</small><br><span style="font-size:1.1em;">{ph_now.strftime('%I:%M %p')}</span></div>
                </div>

                <div style="text-align:left; margin-bottom:5px;"><small style="color:#94a3b8;">LATEST BOT RESPONSE:</small></div>
                <div class="reply-box">{last_bot_reply}</div>

                <div style="text-align:left; margin: 20px 0 5px 0;"><small style="color:#94a3b8;">SYSTEM LOGS:</small></div>
                <div class="log-area">{log_html if log_html else "Waiting for activity..."}</div>
            </div>
        </div>
    </body>
    </html>
    """

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def main_logic():
    global last_sent_time, next_run_time, last_bot_reply, bot_log, total_grows_today
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    async with client:
        while True:
            ph_now = get_ph_time()
            if 7 <= ph_now.hour < 23:
                try:
                    async with client.conversation(TARGET_BOT, timeout=None) as conv:
                        # 1. Typing Phase
                        async with client.action(TARGET_BOT, 'typing'):
                            await asyncio.sleep(random.uniform(3, 7))
                            
                            # 2. Send Command
                            await conv.send_message("/grow")
                            
                            # 3. Wait Phase (Downtime Protected)
                            response = await conv.get_response()
                            
                            # 4. Read Phase (Human Delay)
                            await asyncio.sleep(random.uniform(2, 5))
                            await client.send_read_acknowledge(TARGET_BOT, response)
                            
                            # 5. Global Updates
                            last_sent_time = get_ph_time()
                            last_bot_reply = response.text
                            total_grows_today += 1
                            bot_log.append(f"[{last_sent_time.strftime('%H:%M')}] SUCCESS: Grow completed.")

                except Exception as e:
                    bot_log.append(f"[{get_ph_time().strftime('%H:%M')}] ERROR: {str(e)[:30]}")
                    await asyncio.sleep(30)
                
                # 6. Calculate Next Interval
                wait_seconds = random.randint(45, 90)
                if random.random() < 0.05: # Human break
                    wait_seconds = random.randint(300, 600)
                    bot_log.append(f"[{get_ph_time().strftime('%H:%M')}] System taking coffee break.")
                
                next_run_time = get_ph_time() + timedelta(seconds=wait_seconds)
                await asyncio.sleep(wait_seconds)
            else:
                next_run_time = None
                await asyncio.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_logic())
