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

# --- GLOBAL TRACKING FOR DASHBOARD ---
last_sent_time = None
last_bot_reply = "No reply yet..."
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
    
    # 1. Determine Visual Status
    if not (7 <= ph_hour < 23):
        status_html = "<span style='color: #ff4d4d;'>🔴 SLEEPING (Stealth Night Mode)</span>"
    else:
        status_html = f"<span style='color: #2ecc71;'>🟢 ACTIVE</span> - <small>{bot_status_msg}</small>"
        
    # 2. Format Last Message Time
    time_info = "N/A"
    if last_sent_time:
        diff = ph_now - last_sent_time
        sec = int(diff.total_seconds())
        time_info = f"{sec}s ago" if sec < 60 else f"{sec // 60}m ago"

    # 3. Create Log List
    recent_logs = "".join([f"<li style='margin-bottom:5px;'>{l}</li>" for l in bot_log[-5:]])

    return f"""
    <html>
        <head><title>PH Bot Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; text-align: center; }}
            .card {{ background: white; max-width: 500px; margin: auto; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
            .stat-box {{ background: #f8f9fa; padding: 15px; border-radius: 12px; margin: 15px 0; border-left: 5px solid #3498db; text-align: left; }}
            .bot-msg {{ background: #e3f2fd; padding: 10px; border-radius: 8px; font-style: italic; color: #1565c0; font-size: 0.9em; }}
            .log-box {{ text-align: left; background: #333; color: #00ff00; padding: 15px; border-radius: 10px; font-family: monospace; font-size: 0.8em; overflow: hidden; }}
        </style>
        </head>
        <body>
            <div class="card">
                <h2 style="margin-top:0;">🇵🇭 FkerKey Auto-Grow</h2>
                <div><b>Status:</b> {status_html}</div>
                <p><b>PH Local Time:</b> {ph_now.strftime('%I:%M:%S %p')}</p>
                
                <div class="stat-box">
                    <b>Last Reply from @FkerKeyBot:</b><br>
                    <div class="bot-msg">"{last_bot_reply}"</div>
                </div>

                <div style="display: flex; justify-content: space-around; margin: 20px 0;">
                    <div><b>Grows Today</b><br><span style="font-size: 1.5em; color: #2ecc71;">{total_grows_today}</span></div>
                    <div><b>Last Sent</b><br><span style="font-size: 1.5em; color: #3498db;">{time_info}</span></div>
                </div>

                <div class="log-box">
                    <div style="color: #aaa; margin-bottom: 5px; border-bottom: 1px solid #444;">Recent Activity Logs:</div>
                    <ul style="list-style: none; padding: 0; margin: 0;">{recent_logs if recent_logs else "Waiting for first loop..."}</ul>
                </div>
                <p style="font-size: 0.7em; color: #888; margin-top: 20px;">Safe Hours: 7:00 AM - 11:00 PM PHT</p>
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
        print("Bot logic started with Conversation mode.")
        
        while True:
            ph_now = get_ph_time()
            # Active hours: 7 AM to 11 PM
            if 7 <= ph_now.hour < 23:
                try:
                    # Reset counter if it's a new day (optional)
                    if ph_now.hour == 7 and ph_now.minute < 10: total_grows_today = 0

                    async with client.conversation(TARGET_BOT, timeout=None) as conv:
                        bot_status_msg = "Simulating typing..."
                        async with client.action(TARGET_BOT, 'typing'):
                            await asyncio.sleep(random.uniform(3, 6))
                            
                            # Send message
                            await conv.send_message("/grow")
                            bot_status_msg = "Waiting for @FkerKeyBot reply..."
                            
                            # DOWNTIME PROTECTION: Wait forever until the bot replies
                            response = await conv.get_response()
                            
                            # HUMAN READ SIMULATION: Wait 2-4s before marking as read
                            await asyncio.sleep(random.uniform(2, 4))
                            await client.send_read_acknowledge(TARGET_BOT, response)
                            
                            # Update Global Info
                            last_sent_time = get_ph_time()
                            last_bot_reply = response.text.replace('\\n', ' ')[:100] + ("..." if len(response.text) > 100 else "")
                            total_grows_today += 1
                            
                            log_msg = f"[{last_sent_time.strftime('%I:%M %p')}] Successfully grew!"
                            bot_log.append(log_msg)
                            if len(bot_log) > 10: bot_log.pop(0)

                        bot_status_msg = "Resting between grows..."
                
                except Exception as e:
                    bot_status_msg = "Connection error. Retrying..."
                    print(f"Error: {e}")
                    await asyncio.sleep(60)
                
                # Randomized Interval (45-90 seconds)
                wait_time = random.randint(45, 90)
                # 5% chance of a longer "human break" (5-10 mins)
                if random.random() < 0.05:
                    wait_time = random.randint(300, 600)
                    bot_status_msg = "Taking a short break..."
                
                await asyncio.sleep(wait_time)
            else:
                bot_status_msg = "Sleeping (Night Mode)"
                await asyncio.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main_logic())
