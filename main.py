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
last_bot_reply = "Waiting for first reply..."
bot_log = []
bot_status_msg = "Initializing..."
total_grows_today = 0

app = Flask(__name__)

def get_ph_time():
    return datetime.now(timezone(timedelta(hours=8)))

@app.route('/')
def home():
    ph_now = get_ph_time()
    ph_hour = ph_now.hour
    
    if not (7 <= ph_hour < 23):
        status_html = "<span style='color: #ff4d4d;'>🔴 SLEEPING (Night Mode)</span>"
    else:
        status_html = f"<span style='color: #2ecc71;'>🟢 ACTIVE</span> - <small>{bot_status_msg}</small>"
        
    time_info = "N/A"
    if last_sent_time:
        diff = ph_now - last_sent_time
        sec = int(diff.total_seconds())
        time_info = f"{sec}s ago" if sec < 60 else f"{sec // 60}m ago"

    recent_logs = "".join([f"<li style='margin-bottom:8px; border-bottom:1px solid #444; padding-bottom:4px;'>{l}</li>" for l in bot_log[-8:]])

    return f"""
    <html>
        <head>
            <title>PH Bot Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f0f2f5; margin: 0; padding: 15px; }}
                .card {{ background: white; max-width: 450px; margin: auto; padding: 20px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
                .stat-box {{ background: #f8f9fa; padding: 15px; border-radius: 12px; margin: 15px 0; border-left: 5px solid #3498db; text-align: left; }}
                
                /* FIXED: This section now allows full text wrapping */
                .bot-msg {{ 
                    background: #e3f2fd; 
                    padding: 12px; 
                    border-radius: 8px; 
                    color: #1565c0; 
                    font-size: 0.95em;
                    line-height: 1.4;
                    white-space: pre-wrap;       /* Keeps line breaks from the bot */
                    word-wrap: break-word;       /* Breaks long words if needed */
                    overflow-wrap: break-word;
                    word-break: normal;
                }}
                
                .grid {{ display: flex; justify-content: space-around; margin: 20px 0; border-top: 1px solid #eee; padding-top: 15px; }}
                .log-box {{ text-align: left; background: #222; color: #00ff00; padding: 15px; border-radius: 10px; font-family: 'Courier New', monospace; font-size: 0.85em; }}
                h2 {{ color: #1a1a1a; margin-top: 0; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🇵🇭 Bot Dashboard</h2>
                <div style="margin-bottom: 10px;"><b>Status:</b> {status_html}</div>
                <div style="font-size: 0.9em; color: #666;">PH Time: {ph_now.strftime('%I:%M:%S %p')}</div>
                
                <div class="stat-box">
                    <b style="display:block; margin-bottom:5px;">Last Message from Bot:</b>
                    <div class="bot-msg">{last_bot_reply}</div>
                </div>

                <div class="grid">
                    <div><small>Grows Today</small><br><b style="font-size: 1.4em; color: #2ecc71;">{total_grows_today}</b></div>
                    <div><small>Last Action</small><br><b style="font-size: 1.4em; color: #3498db;">{time_info}</b></div>
                </div>

                <div class="log-box">
                    <div style="color: #888; font-size: 0.8em; margin-bottom: 10px;">ACTIVITY LOG</div>
                    <ul style="list-style: none; padding: 0; margin: 0;">{recent_logs if recent_logs else "Waiting..."}</ul>
                </div>
            </div>
        </body>
    </html>
    """

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def main_logic():
    global last_sent_time, last_bot_reply, bot_log, bot_status_msg, total_grows_today
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    async with client:
        while True:
            ph_now = get_ph_time()
            if 7 <= ph_now.hour < 23:
                try:
                    async with client.conversation(TARGET_BOT, timeout=None) as conv:
                        bot_status_msg = "Typing..."
                        async with client.action(TARGET_BOT, 'typing'):
                            await asyncio.sleep(random.uniform(3, 5))
                            await conv.send_message("/grow")
                            
                            bot_status_msg = "Waiting for reply..."
                            response = await conv.get_response()
                            
                            # Reading simulation
                            await asyncio.sleep(random.uniform(2, 4))
                            await client.send_read_acknowledge(TARGET_BOT, response)
                            
                            # Global Updates
                            last_sent_time = get_ph_time()
                            last_bot_reply = response.text  # Removed the truncation logic
                            total_grows_today += 1
                            
                            bot_log.append(f"🟢 Successfully grew at {last_sent_time.strftime('%I:%M %p')}")
                            if len(bot_log) > 15: bot_log.pop(0)

                        bot_status_msg = "Idle"
                
                except Exception as e:
                    bot_status_msg = "Error. Retrying..."
                    await asyncio.sleep(30)
                
                # Randomized Wait
                wait_time = random.randint(45, 90)
                if random.random() < 0.05: # 5% Human Break
                    wait_time = random.randint(300, 600)
                await asyncio.sleep(wait_time)
            else:
                bot_status_msg = "Sleeping"
                await asyncio.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_logic())
