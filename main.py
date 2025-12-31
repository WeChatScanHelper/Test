import os
import asyncio
import random
import threading
from datetime import datetime, timedelta, timezone
from flask import Flask, request, redirect, url_for
from telethon import TelegramClient, events, errors, functions
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID", 36062585))
API_HASH = os.getenv("API_HASH", "27af3370413767173feb169bec5065f9")
SESSION_STRING = os.getenv("SESSION_STRING") 

GROUP_TARGET = -1003598172312 
MY_USERNAME = "AryaCollymore"   
BOT_USERNAME = "FkerKeyBot"

# --- PERSISTENT TRACKING ---
# Using global variables that act as a "Session Cache"
last_bot_reply = "System Ready."
bot_logs = ["Bot Initialized..."]
total_grows_today = 0
total_grows_yesterday = 0
is_blocked = False 
is_running = True # Control Switch
next_run_time = None
current_day = datetime.now(timezone(timedelta(hours=8))).day

app = Flask(__name__)

def get_ph_time():
    return datetime.now(timezone(timedelta(hours=8)))

def add_log(text):
    global bot_logs
    timestamp = get_ph_time().strftime('%H:%M:%S')
    bot_logs.append(f"[{timestamp}] {text}")
    if len(bot_logs) > 100: # Keep last 100 logs
        bot_logs.pop(0)

@app.route('/')
def home():
    ph_now = get_ph_time()
    
    # Status Logic
    if not is_running:
        status_text, status_color = "🔴 PAUSED", "#ff4d4d"
        countdown_text = "PAUSED"
    elif is_blocked:
        status_text, status_color = "⚠️ MUTED", "#fbbf24"
        countdown_text = "WAITING"
    else:
        status_text, status_color = "🟢 TURBO ACTIVE", "#38bdf8"
        if next_run_time:
            diff = int((next_run_time - ph_now).total_seconds())
            countdown_text = f"{max(0, diff)}s"
        else:
            countdown_text = "..."

    log_html = "".join([f"<div style='border-bottom:1px solid #334155; padding:5px 0;'>{l}</div>" for l in reversed(bot_logs)])

    return f"""
    <html>
    <head>
        <title>PH Turbo Control</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="refresh" content="1">
        <style>
            body {{ font-family: sans-serif; background: #0f172a; color: white; text-align: center; padding: 10px; margin: 0; }}
            .card {{ background: #1e293b; max-width: 500px; margin: auto; padding: 20px; border-radius: 20px; border: 1px solid #475569; }}
            .timer {{ font-size: 3.5em; font-weight: bold; color: {status_color}; margin: 5px 0; }}
            .controls {{ display: flex; gap: 10px; justify-content: center; margin: 20px 0; }}
            .btn {{ padding: 12px 25px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; text-decoration: none; color: white; }}
            .btn-play {{ background: #22c55e; }}
            .btn-stop {{ background: #ef4444; }}
            .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .stat-box {{ background: #0f172a; padding: 10px; border-radius: 10px; }}
            .log-container {{ background: #000; padding: 10px; border-radius: 10px; text-align: left; height: 250px; overflow-y: scroll; font-family: monospace; font-size: 0.8em; color: #4ade80; }}
            .reply-box {{ background: #334155; padding: 10px; border-radius: 10px; text-align: left; font-size: 0.8em; margin: 10px 0; border-left: 4px solid #38bdf8; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div style="font-weight: bold; color: {status_color};">{status_text}</div>
            <div class="timer">{countdown_text}</div>
            
            <div class="controls">
                <a href="/start" class="btn btn-play">▶ PLAY</a>
                <a href="/stop" class="btn btn-stop">■ STOP</a>
            </div>

            <div class="stats-grid">
                <div class="stat-box"><small style="color:#94a3b8">TODAY</small><br><span style="font-size:1.5em">{total_grows_today}</span></div>
                <div class="stat-box"><small style="color:#94a3b8">YESTERDAY</small><br><span style="font-size:1.5em; color:#64748b">{total_grows_yesterday}</span></div>
            </div>

            <div class="reply-box"><b>Bot:</b> {last_bot_reply}</div>

            <div style="text-align:left; font-size:0.7em; color:#94a3b8; margin: 10px 0 5px 0;">SYSTEM LOGS (Scrollable)</div>
            <div class="log-container">{log_html}</div>
        </div>
    </body>
    </html>
    """

@app.route('/start')
def start_bot():
    global is_running
    is_running = True
    add_log("▶ User clicked START")
    return redirect(url_for('home'))

@app.route('/stop')
def stop_bot():
    global is_running, next_run_time
    is_running = False
    next_run_time = None
    add_log("■ User clicked STOP")
    return redirect(url_for('home'))

async def main_logic():
    global last_sent_time, next_run_time, last_bot_reply, total_grows_today, total_grows_yesterday, is_blocked, is_running, current_day
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    @client.on(events.NewMessage(chats=GROUP_TARGET))
    async def handler(event):
        global last_bot_reply
        try:
            await client(functions.messages.ReadMentionsRequest(peer=GROUP_TARGET))
            await client.send_read_acknowledge(event.chat_id, event.message)
        except: pass

        if event.sender_id and str(event.sender.username).lower() == BOT_USERNAME.strip('@').lower():
            if MY_USERNAME.lower() in event.text.lower() and "BATTLE" not in event.text.upper():
                last_bot_reply = event.text
                add_log("Bot response received")

    async with client:
        while True:
            ph_now = get_ph_time()
            
            # Reset daily stats
            if ph_now.day != current_day:
                total_grows_yesterday = total_grows_today
                total_grows_today = 0
                current_day = ph_now.day
                add_log("Midnight Reset: Stats updated")

            if is_running:
                try:
                    async with client.action(GROUP_TARGET, 'typing'):
                        await asyncio.sleep(random.uniform(2, 4))
                        await client.send_message(GROUP_TARGET, "/grow")
                        is_blocked = False 
                        total_grows_today += 1
                        add_log(f"Sent /grow (Total: {total_grows_today})")

                except (errors.ChatWriteForbiddenError, errors.ChatAdminRequiredError):
                    is_blocked = True
                    add_log("⚠️ Error: Muted in Group")
                    await asyncio.sleep(300)
                    continue
                except Exception as e:
                    add_log(f"Error: {str(e)[:20]}")
                    await asyncio.sleep(30)

                next_run_time = get_ph_time() + timedelta(seconds=35)
                await asyncio.sleep(35)
            else:
                await asyncio.sleep(2) # Idle wait when stopped

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_logic())
