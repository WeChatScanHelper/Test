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
last_bot_reply = "System Standby..."
bot_logs = ["UI Framework Updated to Responsive Design."]
total_grows_today = 0
total_grows_yesterday = 0
is_blocked = False 
is_running = True 
next_run_time = None
force_trigger = False 
current_day = datetime.now(timezone(timedelta(hours=8))).day

app = Flask(__name__)

def get_ph_time():
    return datetime.now(timezone(timedelta(hours=8)))

def add_log(text):
    global bot_logs
    timestamp = get_ph_time().strftime('%H:%M:%S')
    bot_logs.append(f"[{timestamp}] {text}")
    if len(bot_logs) > 60:
        bot_logs.pop(0)

@app.route('/')
def home():
    ph_now = get_ph_time()
    
    if not is_running:
        status_text, status_color = "PAUSED", "#f87171"
        countdown_text = "OFF"
    elif is_blocked:
        status_text, status_color = "MUTED / ERROR", "#fbbf24"
        countdown_text = "WAIT"
    else:
        status_text, status_color = "ACTIVE", "#34d399"
        if next_run_time:
            diff = int((next_run_time - ph_now).total_seconds())
            countdown_text = f"{max(0, diff)}s"
        else:
            countdown_text = "0s"

    log_html = "".join([f"<div class='log-entry'>{l}</div>" for l in reversed(bot_logs)])

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>PH Turbo Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta http-equiv="refresh" content="1">
        <style>
            :root {{
                --bg: #0f172a;
                --card-bg: #1e293b;
                --accent: #38bdf8;
                --text-main: #f8fafc;
                --text-dim: #94a3b8;
            }}
            * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
            body {{ 
                font-family: 'Inter', -apple-system, sans-serif; 
                background: var(--bg); 
                color: var(--text-main); 
                margin: 0; 
                display: flex; 
                justify-content: center; 
                align-items: center;
                min-height: 100vh;
                padding: 15px;
            }}
            .container {{ width: 100%; max-width: 480px; }}
            .card {{ 
                background: var(--card-bg); 
                padding: 24px; 
                border-radius: 24px; 
                border: 1px solid #334155; 
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            }}
            .status-line {{ font-size: 0.75rem; font-weight: 800; letter-spacing: 0.1em; color: {status_color}; margin-bottom: 8px; }}
            .timer {{ font-size: 4rem; font-weight: 900; color: var(--text-main); margin: 0; line-height: 1; }}
            
            .controls {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 24px 0; }}
            .btn {{ 
                padding: 14px; border-radius: 12px; border: none; font-weight: 700; 
                cursor: pointer; text-decoration: none; color: white; font-size: 0.85rem;
                display: flex; align-items: center; justify-content: center; transition: transform 0.1s;
            }}
            .btn:active {{ transform: scale(0.96); }}
            .btn-play {{ background: #059669; }}
            .btn-stop {{ background: #dc2626; }}
            .btn-restart {{ background: var(--accent); grid-column: span 2; }}

            .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
            .stat-box {{ background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 16px; border: 1px solid #334155; }}
            .stat-val {{ font-size: 1.5rem; font-weight: 800; display: block; }}
            .stat-lbl {{ font-size: 0.65rem; color: var(--text-dim); font-weight: 700; text-transform: uppercase; }}

            .reply-box {{ 
                background: #0f172a; padding: 16px; border-radius: 16px; text-align: left; 
                font-size: 0.85rem; margin: 20px 0; border-left: 4px solid var(--accent);
                overflow-wrap: break-word; line-height: 1.4;
            }}
            .log-container {{ 
                background: #000; padding: 12px; border-radius: 12px; text-align: left; 
                height: 180px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; 
                font-size: 0.75rem; color: #4ade80; border: 1px solid #334155;
            }}
            .log-entry {{ border-bottom: 1px solid #1e293b; padding: 4px 0; }}
            
            @media (max-width: 360px) {{
                .timer {{ font-size: 3rem; }}
                .card {{ padding: 16px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="status-line">{status_text}</div>
                <div class="timer">{countdown_text}</div>
                
                <div class="controls">
                    <a href="/start" class="btn btn-play">RESUME</a>
                    <a href="/stop" class="btn btn-stop">PAUSE</a>
                    <a href="/restart" class="btn btn-restart">🔄 FORCE RESTART / UNMUTE</a>
                </div>

                <div class="stats-grid">
                    <div class="stat-box">
                        <span class="stat-lbl">Today</span>
                        <span class="stat-val">{total_grows_today}</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-lbl">Yesterday</span>
                        <span class="stat-val" style="color: var(--text-dim)">{total_grows_yesterday}</span>
                    </div>
                </div>

                <div class="reply-box">
                    <span class="stat-lbl" style="margin-bottom:4px; display:block;">Bot Response</span>
                    {last_bot_reply}
                </div>

                <div class="stat-lbl" style="text-align:left; margin-bottom: 8px;">System Events</div>
                <div class="log-container">{log_html}</div>
            </div>
        </div>
    </body>
    </html>
    """

# ... [The Flask Routes /start, /stop, /restart remain identical to the previous block] ...

@app.route('/start')
def start_bot():
    global is_running
    is_running = True
    add_log("User manually started the bot.")
    return redirect(url_for('home'))

@app.route('/stop')
def stop_bot():
    global is_running, next_run_time
    is_running = False
    next_run_time = None
    add_log("User manually paused the bot.")
    return redirect(url_for('home'))

@app.route('/restart')
def restart_bot():
    global is_blocked, force_trigger, is_running
    is_blocked = False
    is_running = True
    force_trigger = True
    add_log("Manual Override Triggered.")
    return redirect(url_for('home'))

async def main_logic():
    global last_sent_time, next_run_time, last_bot_reply, total_grows_today, total_grows_yesterday, is_blocked, is_running, current_day, force_trigger
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

    async with client:
        while True:
            ph_now = get_ph_time()
            if ph_now.day != current_day:
                total_grows_yesterday = total_grows_today
                total_grows_today = 0
                current_day = ph_now.day

            if is_running:
                try:
                    async with client.action(GROUP_TARGET, 'typing'):
                        await asyncio.sleep(random.uniform(2, 4))
                        await client.send_message(GROUP_TARGET, "/grow")
                        is_blocked = False 
                        total_grows_today += 1
                        add_log(f"Sent /grow. Total: {total_grows_today}")

                except (errors.ChatWriteForbiddenError, errors.ChatAdminRequiredError):
                    is_blocked = True
                    add_log("⚠️ Muted. Use Force Restart.")
                except Exception as e:
                    add_log(f"Error: {str(e)[:20]}")

                next_run_time = get_ph_time() + timedelta(seconds=35)
                for _ in range(35):
                    if force_trigger:
                        force_trigger = False
                        break
                    await asyncio.sleep(1)
            else:
                await asyncio.sleep(2)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_logic())
