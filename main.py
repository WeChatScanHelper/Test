import os
import asyncio
import random
import threading
import re
from datetime import datetime, timedelta, timezone
from flask import Flask, request, redirect, url_for, jsonify
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
last_bot_reply = "System Off."
bot_logs = ["Hard Stop logic active. Click RESUME to listen."]
total_grows_today = 0
total_grows_yesterday = 0
waits_today = 0
waits_yesterday = 0
points_today = 0
points_yesterday = 0
points_lifetime = 0  
is_blocked = False 
is_running = False  
next_run_time = None
force_trigger = False 
current_day = datetime.now(timezone(timedelta(hours=8))).day

app = Flask(__name__)

def get_ph_time():
    return datetime.now(timezone(timedelta(hours=8)))

def add_log(text):
    global bot_logs
    timestamp = get_ph_time().strftime('%H:%M:%S')
    bot_logs.insert(0, f"[{timestamp}] {text}")
    if len(bot_logs) > 50: bot_logs.pop()

# --- WEB UI ---
@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>PH Turbo Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            :root { --bg: #0f172a; --card: #1e293b; --acc: #38bdf8; --text: #f8fafc; }
            body { font-family: sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 10px; display: flex; justify-content: center; }
            .card { width: 100%; max-width: 500px; background: var(--card); padding: 20px; border-radius: 24px; border: 1px solid #334155; }
            .timer { font-size: 3.5rem; font-weight: 900; text-align: center; margin: 5px 0; }
            .status-badge { font-size: 0.7rem; font-weight: 800; text-align: center; margin-bottom: 10px; text-transform: uppercase; }
            .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 15px 0; }
            .stat-box { background: rgba(0,0,0,0.2); padding: 10px; border-radius: 12px; border: 1px solid #334155; }
            .stat-val { font-size: 1.2rem; font-weight: 800; display: block; }
            .label { font-size: 0.55rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; }
            .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 15px; }
            .btn { padding: 12px; border-radius: 10px; border: none; font-weight: 800; cursor: pointer; color: white; font-size: 0.75rem; transition: 0.2s; }
            .log-box { background: #000; height: 160px; overflow-y: auto; padding: 10px; font-family: monospace; font-size: 0.7rem; border-radius: 10px; color: #4ade80; border: 1px solid #334155; }
            .reply { background: #0f172a; padding: 10px; border-radius: 10px; font-size: 0.8rem; border-left: 4px solid var(--acc); margin: 12px 0; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <div class="card">
            <div id="status" class="status-badge">...</div>
            <div class="timer" id="timer">--</div>
            <div class="btn-group">
                <button onclick="fetch('/start')" class="btn" style="background:#059669">▶ RESUME</button>
                <button onclick="fetch('/stop')" class="btn" style="background:#dc2626">■ STOP</button>
                <button onclick="fetch('/restart')" class="btn" style="background:#38bdf8">🔄 FORCE</button>
                <button onclick="fetch('/clear_logs')" class="btn" style="background:#64748b">🧹 CLEAR</button>
            </div>
            <div class="stats-grid">
                <div class="stat-box" style="grid-column: span 2; text-align: center; border-color: var(--acc);">
                    <span class="label" style="color: var(--acc);">Lifetime Total Points</span>
                    <span id="pl" class="stat-val" style="font-size: 1.6rem;">0</span>
                </div>
                <div class="stat-box"><span class="label">Pts Today</span><span id="pt" class="stat-val" style="color:#4ade80">+0</span></div>
                <div class="stat-box"><span class="label">Pts Yesterday</span><span id="py" class="stat-val">+0</span></div>
                <div class="stat-box"><span class="label">Grow Today</span><span id="gt" class="stat-val">0</span></div>
                <div class="stat-box"><span class="label">Grow Yesterday</span><span id="gy" class="stat-val">0</span></div>
                <div class="stat-box"><span class="label">Wait Today</span><span id="wt" class="stat-val" style="color:#fbbf24">0</span></div>
                <div class="stat-box"><span class="label">Wait Yesterday</span><span id="wy" class="stat-val">0</span></div>
            </div>
            <div class="label">Latest Bot Response</div>
            <div class="reply" id="reply">...</div>
            <div class="log-box" id="logs"></div>
        </div>
        <script>
            async function update() {
                try {
                    const res = await fetch('/api/data');
                    const d = await res.json();
                    document.getElementById('timer').innerText = d.timer;
                    document.getElementById('gt').innerText = d.gt;
                    document.getElementById('gy').innerText = d.gy;
                    document.getElementById('wt').innerText = d.wt;
                    document.getElementById('wy').innerText = d.wy;
                    document.getElementById('pt').innerText = '+' + d.pt;
                    document.getElementById('py').innerText = '+' + d.py;
                    document.getElementById('pl').innerText = d.pl.toLocaleString();
                    document.getElementById('reply').innerText = d.reply;
                    document.getElementById('status').innerText = d.status;
                    document.getElementById('status').style.color = d.color;
                    document.getElementById('logs').innerHTML = d.logs.map(l => `<div>${l}</div>`).join('');
                } catch (e) {}
            }
            setInterval(update, 1000);
        </script>
    </body>
    </html>
    """

@app.route('/api/data')
def get_data():
    ph_now = get_ph_time()
    t_str = "--"
    if not is_running: s, c, t_str = "🛑 STOPPED", "#f87171", "OFF"
    elif is_blocked: s, c, t_str = "⚠️ MUTED", "#fbbf24", "MUTE"
    else:
        s, c = "🟢 ACTIVE", "#34d399"
        if next_run_time:
            diff = int((next_run_time - ph_now).total_seconds())
            t_str = f"{max(0, diff)}s"
    return jsonify({
        "timer": t_str, "gt": total_grows_today, "gy": total_grows_yesterday,
        "pt": points_today, "py": points_yesterday, "pl": points_lifetime, 
        "wt": waits_today, "wy": waits_yesterday,
        "reply": last_bot_reply, "status": s, "color": c, "logs": bot_logs
    })

@app.route('/start')
def start_bot(): 
    global is_running, force_trigger
    is_running = True
    force_trigger = True
    add_log("▶ RESUME: Commands & Listener Re-Activated.")
    return "OK"

@app.route('/stop')
def stop_bot(): 
    global is_running, next_run_time
    is_running = False
    next_run_time = None
    add_log("■ STOP: System is now Deaf & Mute.")
    return "OK"

@app.route('/restart')
def restart_bot(): 
    global is_blocked, force_trigger, is_running
    is_blocked = False; is_running = True; force_trigger = True
    add_log("🔄 FORCE: Attempting immediate grow.")
    return "OK"

@app.route('/clear_logs')
def clear_logs(): 
    global bot_logs; bot_logs = ["Logs cleared."]; return "OK"

async def main_logic():
    global last_bot_reply, total_grows_today, total_grows_yesterday, waits_today, waits_yesterday, points_today, points_yesterday, points_lifetime, is_blocked, is_running, current_day, force_trigger, next_run_time
    
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    # --- THE VERIFICATION HANDLER ---
    async def handler(event):
        global last_bot_reply, points_today, points_lifetime, total_grows_today, waits_today
        # Even if the handler is attached, this double-check ensures silence when stopped
        if not is_running: return 

        if event.sender_id and str(event.sender.username).lower() == BOT_USERNAME.strip('@').lower():
            msg = event.text
            if MY_USERNAME.lower() in msg.lower() and "BATTLE" not in msg.upper():
                last_bot_reply = msg
                if "please wait" in msg.lower():
                    waits_today += 1
                    add_log("❌ Verification: WAIT (Not Counted)")
                elif "GROW SUCCESS" in msg.upper() or "Gained:" in msg:
                    total_grows_today += 1
                    match = re.search(r'Gained:\s*([+-]\d+)', msg)
                    if match:
                        val = int(match.group(1))
                        points_today += val
                        points_lifetime += val
                        add_log(f"✅ Verified: Grow #{total_grows_today} (+{val} pts)")

    async with client:
        add_log("Connected to Telegram.")
        listener_active = False

        while True:
            ph_now = get_ph_time()
            if ph_now.day != current_day:
                total_grows_yesterday, waits_yesterday, points_yesterday = total_grows_today, waits_today, points_today
                total_grows_today, waits_today, points_today = 0, 0, 0
                current_day = ph_now.day

            # --- DYNAMIC LISTENER CONTROL ---
            if is_running and not listener_active:
                client.add_event_handler(handler, events.NewMessage(chats=GROUP_TARGET))
                listener_active = True
                add_log("📡 Listener attached.")
            elif not is_running and listener_active:
                client.remove_event_handler(handler)
                listener_active = False
                add_log("🔇 Listener detached.")

            if is_running:
                try:
                    add_log("🚀 Sending command: /grow")
                    async with client.action(GROUP_TARGET, 'typing'):
                        await asyncio.sleep(random.uniform(2, 4))
                        await client.send_message(GROUP_TARGET, "/grow")
                        is_blocked = False
                except Exception as e:
                    is_blocked = True
                    add_log(f"⚠️ Muted: {str(e)[:20]}")

                next_run_time = get_ph_time() + timedelta(seconds=35)
                for _ in range(35):
                    if force_trigger or not is_running:
                        force_trigger = False
                        break
                    await asyncio.sleep(1)
            else:
                await asyncio.sleep(1)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_logic())
