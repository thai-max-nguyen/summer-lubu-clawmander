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
import os, sys, time, json, random, urllib.request, urllib.parse

LLM_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE = os.environ.get("LLM_BASE_URL", "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemma-4-31b-it")
TG_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TG_CHAT_ID", "")
INTERVAL = int(os.environ.get("INTERVAL_SEC", "30"))
TARGET = os.environ.get("TARGET_NAME", "Khải")

# Diversity pools — random-pick each call so the roast never feels samey.
_DOMAINS = [
    "một triết gia phương Tây (Socrates, Nietzsche, Aristotle, Seneca...)",
    "một nhà khoa học (Einstein, Newton, Darwin, Marie Curie, Hawking...)",
    "một doanh nhân công nghệ (Steve Jobs, Bill Gates, Elon Musk, Jeff Bezos...)",
    "một võ sư hoặc vận động viên (Lý Tiểu Long, Muhammad Ali, Michael Jordan...)",
    "một nhà văn / nghệ sĩ (Shakespeare, Picasso, Mark Twain, Oscar Wilde...)",
    "một danh nhân lịch sử (Gandhi, Lincoln, Napoleon, Churchill...)",
    "triết lý phương Đông (Khổng Tử, Lão Tử, Tôn Tử, Đức Phật...)",
    "một nhân vật / câu nói dân gian Việt Nam hoặc tục ngữ ca dao",
]
_TOPICS = [
    "lười biếng, hay trì hoãn", "tiêu tiền hoang phí", "thức khuya cày phim",
    "trễ deadline", "mãi chưa có người yêu / ế bền vững", "ăn uống vô độ",
    "sống ảo, nghiện mạng xã hội", "lười tập thể dục", "ngủ nướng",
    "hứa rồi không làm", "đầu tư đu đỉnh", "cả thèm chóng chán",
]
_STYLES = [
    "cà khịa nhẹ nhàng", "an ủi kiểu giả trân rồi quay xe",
    "so sánh hài hước phóng đại", "làm bộ nghiêm túc triết lý rồi chốt hạ bất ngờ",
    "giọng ông bà dạy cháu", "kiểu thầy bói phán",
]


def _prompt():
    dom = random.choice(_DOMAINS); top = random.choice(_TOPICS); sty = random.choice(_STYLES)
    return (
        f"Bạn là 'Thanh Niên Đạo Lý' — bot hài hước chuyên 'dạy đời' bạn {TARGET}. "
        f"Lần này hãy trích MỘT câu nói nổi tiếng CÓ THẬT của {dom}, "
        f"rồi cà khịa {TARGET} về thói {top}, theo phong cách {sty}. "
        "Viết MỘT tin nhắn tiếng Việt vui, KHÔNG xúc phạm, KHÔNG tục, theo mẫu:\n"
        f"\"Nghe <tên người> nói nè {TARGET}: '<câu nói>'. <câu chêm đạo lý hài hước>. "
        "Đừng sống lỗi nữa nha 😌🦞\"\n"
        "QUAN TRỌNG: chọn người nổi tiếng và câu nói MỚI, KHÁC những lần trước, "
        "tránh lặp lại Einstein. CHỈ xuất ra tin nhắn, không thêm gì khác.")


def gemma_quote():
    body = json.dumps({
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": _prompt()}],
        "max_tokens": 120, "temperature": 1.35, "top_p": 0.95,
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
        import datetime
        fast_until = os.environ.get("FAST_UNTIL", "2026-06-10")   # today: fast cadence
        fast = int(os.environ.get("FAST_INTERVAL", "120"))         # 2 min today
        slow = int(os.environ.get("SLOW_INTERVAL", "43200"))       # 12h after today

        def interval():
            return fast if datetime.date.today().isoformat() <= fast_until else slow
        print(f"loop → {fast}s until {fast_until}, then {slow}s · chat {TG_CHAT}")
        while True:
            try:
                post_one()
            except Exception as e:
                print("err:", e)
            time.sleep(interval())
    else:
        return 0 if post_one() else 1


if __name__ == "__main__":
    sys.exit(main())
