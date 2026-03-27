

import os
import random
import asyncio
import logging
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.errors import UserAlreadyParticipant, FloodWait, PeerIdInvalid, BadRequest, Forbidden

# --- FALTU LOGS HIDE KARNE KE LIYE ---
logging.getLogger("pyrogram").setLevel(logging.CRITICAL)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# --- CONFIGURATION (Directly Edit Here) ---
API_ID = 36282226
API_HASH = "72f6e7f5fe68e4f859e86a4b7b4549bd"
OWNER_ID = 8581311255 

# Apni saari 50+ sessions yahan is list mein daal do
SESSION_STRINGS = [
    "BQFouykAHRk-AidGZPMilbqogfbbyHmGIaFGAi...",
    "BQFouykAM3ooku7Fb6B3XiOO1hluZqxvtfO1LK...",
    "BQFouykARHVvE-BayrtLvo9LYgdvNYXLd8RnzT...",
    "BQFouykAuKACQJRMFnKIjYoMW1TL0CXUgE-rkB...",
    # Baaki sessions yahan add karte jao...
]

# --- PROXY LOADER ---
def load_proxies():
    proxies = []
    if os.path.exists("proxies.txt"):
        with open("proxies.txt", "r") as f:
            for line in f:
                p = line.strip().split(":")
                if len(p) == 4:
                    proxies.append({
                        "scheme": "socks5", # Change to "http" if needed
                        "hostname": p[0],
                        "port": int(p[1]),
                        "username": p[2],
                        "password": p[3]
                    })
    return proxies

ALL_PROXIES = load_proxies()

def get_proxy(index):
    if not ALL_PROXIES:
        return None
    return ALL_PROXIES[index % len(ALL_PROXIES)]

# --- FLASK SERVER (For Render Health Check) ---
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running 24/7"

def run_web():
    # Render uses dynamic port, default to 8080
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

# --- BOT LOGIC ---
clients = []

async def join_handler(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Usage:** `/insert [group_link]`")
        return

    join_target = message.command[1]
    status_msg = await message.reply_text("⏳ **Safe-Join Mode Active...**")

    # Shuffle for natural behavior
    temp_clients = list(enumerate(clients))
    random.shuffle(temp_clients)

    joined, already_in, failed = 0, 0, 0
    
    for i, (orig_idx, cli) in enumerate(temp_clients):
        try:
            # First check if already member
            try:
                await cli.get_chat(join_target)
                already_in += 1
            except (BadRequest, Forbidden, PeerIdInvalid):
                # If not member, then join
                await cli.join_chat(join_target)
                joined += 1
                # Antiban Delay: 50 IDs ke liye 1-2 min gap zaroori hai
                if i < len(temp_clients) - 1:
                    await asyncio.sleep(random.randint(60, 150)) 
        except UserAlreadyParticipant:
            already_in += 1
        except FloodWait as e:
            # Agar flood wait aaye toh skip nahi, wait karenge
            await asyncio.sleep(e.value + 5)
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ **Task Completed!**\n\n"
        f"➕ Joined: {joined}\n"
        f"✔️ Already Member: {already_in}\n"
        f"❌ Failed: {failed}"
    )


async def main():
    print("🚀 Starting Userbots... Please wait.")
    
    # Start web server for Render in background
    Thread(target=run_web, daemon=True).start()
    
    for i, session in enumerate(SESSION_STRINGS):
        try:
            p_config = get_proxy(i)
            cli = Client(
                name=f"bot_{i}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session,
                proxy=p_config,
                in_memory=True,
                no_updates=(i != 0) # Only first ID listens to commands
            )
            
            if i == 0:
                # Sirf pehli ID (Master) par command chalega
                cli.add_handler(filters.command("insert", prefixes=["/", ".", "!"]) & filters.user(OWNER_ID))(join_handler)
                
            await cli.start()
            clients.append(cli)
            mode = "Proxy" if p_config else "No Proxy"
            print(f"✅ Account {i+1} Online ({mode})")
        except Exception as e:
            print(f"❌ Account {i+1} Failed: {e}")

    print("\n💎 Multi-Joiner is LIVE on Render!")
    await idle()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping...")
