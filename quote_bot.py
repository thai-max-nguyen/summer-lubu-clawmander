#!/usr/bin/env python3
"""Summer Lubu Clawmander — famous-quote bot.

Every minute, asks Gemma (GreenNode AI Platform) for a famous quote and posts
it to the Clawathon Telegram group.

Env (all required except interval):
  LLM_API_KEY    GreenNode AIP API key
  LLM_BASE_URL   https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1
  LLM_MODEL      google/gemma-4-31b-it
  TG_BOT_TOKEN   Telegram bot token (@summer_lubu_bot)
  TG_CHAT_ID     Clawathon group chat id
  INTERVAL_SEC   default 60

Usage:
  python3 quote_bot.py once     # post a single quote
  python3 quote_bot.py loop     # post every INTERVAL_SEC (AgentBase runtime)
"""
import os, sys, time, json, urllib.request, urllib.parse

LLM_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE = os.environ.get("LLM_BASE_URL", "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemma-4-31b-it")
TG_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TG_CHAT_ID", "")
INTERVAL = int(os.environ.get("INTERVAL_SEC", "30"))
TARGET = os.environ.get("TARGET_NAME", "Khải")

PROMPT = (
    f"Bạn là 'Thanh Niên Đạo Lý' — một bot hài hước chuyên đi 'dạy đời' bạn {TARGET} "
    "bằng những câu nói nổi tiếng. Viết MỘT tin nhắn ngắn bằng tiếng Việt, vui và cà "
    "khịa nhẹ nhàng (KHÔNG xúc phạm, KHÔNG tục), theo đúng mẫu:\n"
    f"\"Nghe <tên người nổi tiếng> nói nè {TARGET}: '<câu nói nổi tiếng có thật của họ>'. "
    "<một câu chêm đạo lý hài hước>. Đừng sống lỗi nữa nha 😌🦞\"\n"
    "Mỗi lần chọn một người nổi tiếng + câu nói KHÁC nhau (Einstein, Khổng Tử, Steve Jobs, "
    "Lý Tiểu Long, Aristotle, Gandhi...). CHỈ xuất ra tin nhắn, không thêm gì khác.")


def gemma_quote():
    body = json.dumps({
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 80, "temperature": 1.1,
    }).encode()
    req = urllib.request.Request(f"{LLM_BASE}/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {LLM_KEY}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"].strip()


def tg_send(text):
    data = urllib.parse.urlencode({"chat_id": TG_CHAT, "text": text}).encode()
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=25) as r:
                return json.loads(r.read()).get("ok", False)
        except Exception:
            time.sleep(2)
    return False


def post_one():
    q = gemma_quote()
    msg = f"💬 {q}\n\n— 🦞 Summer Lubu Clawmander (via Gemma)"
    ok = tg_send(msg)
    print(("sent ✓ " if ok else "FAILED ") + q)
    return ok


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if not (LLM_KEY and TG_TOKEN and TG_CHAT):
        print("Missing env: LLM_API_KEY / TG_BOT_TOKEN / TG_CHAT_ID"); return 1
    if mode == "loop":
        print(f"loop every {INTERVAL}s → chat {TG_CHAT}, model {LLM_MODEL}")
        while True:
            try:
                post_one()
            except Exception as e:
                print("err:", e)
            time.sleep(INTERVAL)
    else:
        return 0 if post_one() else 1


if __name__ == "__main__":
    sys.exit(main())
