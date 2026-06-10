#!/usr/bin/env python3
"""Summer Lubu Clawmander — minimal Telegram bot.

Usage:
  export TG_BOT_TOKEN='123456:ABC...'        # from @BotFather
  python3 telegram_bot.py find               # discover the group chat_id (after adding bot + sending any msg in the group)
  python3 telegram_bot.py send "your text"   # send to TG_CHAT_ID (or first group found)
  python3 telegram_bot.py test               # fire a hello test message
"""
import os, sys, json, urllib.request, urllib.parse

TOKEN = os.environ.get("TG_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TG_CHAT_ID", "")
API = f"https://api.telegram.org/bot{TOKEN}"


def call(method, **params):
    url = f"{API}/{method}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read())


def find_chat():
    """List chats the bot has seen (needs the bot added to the group + one
    message sent there so getUpdates returns it)."""
    d = call("getUpdates")
    seen = {}
    for u in d.get("result", []):
        ch = (u.get("message") or u.get("my_chat_member") or {}).get("chat") or {}
        if ch.get("id"):
            seen[ch["id"]] = ch.get("title") or ch.get("username") or ch.get("type")
    return seen


def main():
    if not TOKEN:
        print("Set TG_BOT_TOKEN first (from @BotFather)."); return 1
    cmd = sys.argv[1] if len(sys.argv) > 1 else "test"
    if cmd == "find":
        for cid, title in find_chat().items():
            print(f"chat_id={cid}  title={title}")
        return 0
    chat = CHAT_ID or next(iter(find_chat()), None)
    if not chat:
        print("No chat_id. Add the bot to the group, send any message there, then run `find`."); return 1
    text = (sys.argv[2] if cmd == "send" and len(sys.argv) > 2
            else "🦞 Summer Lubu Clawmander online! Bot test ok — ready for Claw-a-thon. 🚀")
    r = call("sendMessage", chat_id=chat, text=text)
    print("sent ✓" if r.get("ok") else f"failed: {r}")
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
