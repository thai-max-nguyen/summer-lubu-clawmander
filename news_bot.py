#!/usr/bin/env python3
"""Summer Lubu — VnExpress economy news bot (@khai_xam_lz_bot).

Fetches the top 5 economy articles from VnExpress, summarizes them in ~100
words with Gemma (GreenNode AI Platform), posts to the Telegram group.

Env:
  LLM_API_KEY, LLM_BASE_URL, LLM_MODEL   GreenNode AIP (model google/gemma-4-31b-it)
  TG_BOT_TOKEN  Telegram bot token (@khai_xam_lz_bot)
  TG_CHAT_ID    Clawathon group chat id
  RSS_URL       default VnExpress kinh-doanh
  INTERVAL_SEC  for loop mode (default 1800 = 30 min)

Usage: python3 news_bot.py once | loop
"""
import os, sys, re, html, time, json, urllib.request, urllib.parse

LLM_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE = os.environ.get("LLM_BASE_URL", "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemma-4-31b-it")
TG_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TG_CHAT_ID", "")
RSS_URL = os.environ.get("RSS_URL", "https://vnexpress.net/rss/kinh-doanh.rss")
INTERVAL = int(os.environ.get("INTERVAL_SEC", "1800"))


def _get(url, timeout=25, retries=3):
    last = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e; time.sleep(2)
    raise last


def top_articles(n=5):
    x = _get(RSS_URL).decode("utf-8", "ignore")
    items = re.findall(r"<item>(.*?)</item>", x, re.S)[:n]
    out = []
    for it in items:
        t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
        d = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", it, re.S)
        title = html.unescape(re.sub("<[^>]+>", "", t.group(1)).strip()) if t else ""
        desc = html.unescape(re.sub("<[^>]+>", "", d.group(1)).strip()) if d else ""
        out.append((title, desc))
    return out


def summarize(arts):
    bullets = "\n".join(f"{i}. {t}. {d}" for i, (t, d) in enumerate(arts, 1))
    prompt = ("Dưới đây là 5 tin kinh tế mới nhất từ VnExpress. Hãy viết MỘT bản tóm tắt "
              "tiếng Việt khoảng 100 từ, mạch lạc, dễ đọc, nêu các điểm chính (không liệt kê "
              "thô, viết thành đoạn). Chỉ xuất ra bản tóm tắt:\n\n" + bullets)
    body = json.dumps({"model": LLM_MODEL,
                       "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 260, "temperature": 0.6}).encode()
    req = urllib.request.Request(f"{LLM_BASE}/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {LLM_KEY}",
                                          "Content-Type": "application/json"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"].strip()
        except Exception:
            time.sleep(2)
    raise RuntimeError("LLM failed")


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
    arts = top_articles(5)
    summary = summarize(arts)
    titles = "\n".join(f"{i}. {t}" for i, (t, _) in enumerate(arts, 1))
    msg = (f"📰 TOP 5 TIN KINH TẾ — VnExpress\n\n{summary}\n\n"
           f"— Tiêu đề —\n{titles}\n\n🦞 Summer Lubu · Gemma @ GreenNode")
    ok = tg_send(msg)
    print("sent ✓" if ok else "FAILED")
    return ok


def main():
    if not (LLM_KEY and TG_TOKEN and TG_CHAT):
        print("Missing env."); return 1
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if mode == "loop":
        while True:
            try: post_one()
            except Exception as e: print("err:", e)
            time.sleep(INTERVAL)
    return 0 if post_one() else 1


if __name__ == "__main__":
    sys.exit(main())
