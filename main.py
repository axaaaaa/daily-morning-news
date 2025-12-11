# -*- coding: utf-8 -*-
import requests
import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
import datetime
import time

# 伪装浏览器头，防止第三方统计网站拦截
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

# =============================================================================
# 1. HackRead (RSS)
# =============================================================================
def get_hackread():
    news_list = []
    print(">>> 正在获取 HackRead...")
    try:
        feed = feedparser.parse("https://hackread.com/feed/")
        for entry in feed.entries[:8]:
            pub_date = "Today"
            if hasattr(entry, 'published_parsed'):
                dt = datetime.datetime(*entry.published_parsed[:6])
                pub_date = dt.strftime("%m-%d")
            
            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "date": pub_date
            })
    except:
        news_list.append({"title": "HackRead 获取失败", "link": "#", "date": "Err"})
    return news_list

# =============================================================================
# 2. The Hacker News (RSS)
# =============================================================================
def get_thehackernews():
    news_list = []
    print(">>> 正在获取 The Hacker News...")
    try:
        feed = feedparser.parse("https://feeds.feedburner.com/TheHackersNews")
        for entry in feed.entries[:8]:
            pub_date = "Today"
            if hasattr(entry, 'published_parsed'):
                dt = datetime.datetime(*entry.published_parsed[:6])
                pub_date = dt.strftime("%m-%d")

            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "date": pub_date
            })
    except:
        news_list.append({"title": "THN 获取失败", "link": "#", "date": "Err"})
    return news_list

# =============================================================================
# 3. Hacker News (API)
# =============================================================================
def get_hacker_news():
    news = []
    print(">>> 正在获取 Hacker News (YC)...")
    try:
        ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:8]
        for i in ids:
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json", timeout=5).json()
            if item:
                news.append({
                    "title": item.get('title'),
                    "link": item.get('url', f"https://news.ycombinator.com/item?id={i}"),
                    "score": f"🔥{item.get('score', 0)}"
                })
    except:
        news.append({"title": "HN API 连接失败", "link": "#", "score": "Err"})
    return news



# =============================================================================
# 生成 HTML
# =============================================================================
def generate_html(hackread, thn, hn, x_trends, yt_trends, finance):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 基础列表生成
    hackread_html = "".join([f'<li><span class="date">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in hackread])
    thn_html = "".join([f'<li><span class="date" style="color:#1abc9c;">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in thn])
    hn_html = "".join([f'<li><span class="date" style="color:#f39c12;font-weight:bold;">{n["score"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in hn])
    

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Geek Dashboard</title>
        <style>
            :root {{ --bg: #f4f6f8; --card: #ffffff; --text: #2c3e50; --link: #34495e; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; font-size: 13px; }}
            
            .container {{ max-width: 1200px; margin: 0 auto; }}
            
            header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px; border-bottom: 2px solid #e1e4e8; padding-bottom: 10px; }}
            h1 {{ margin: 0; font-size: 1.5em; color: #34495e; letter-spacing: -0.5px; }}
            .time {{ color: #95a5a6; font-family: monospace; }}
            
            /* 布局：3列 */
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px; }}
            
            .card {{ background: var(--card); padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); border: 1px solid #e1e4e8; }}
            .card h2 {{ margin: 0 0 12px 0; font-size: 1.1em; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; color: #2c3e50; }}
            
            /* 板块颜色定义 */
            .hackread h2 {{ border-color: #e74c3c; }} /* 红 */
            .thn h2 {{ border-color: #1abc9c; }}      /* 青 */
            .hn h2 {{ border-color: #f39c12; }}       /* 橙 */
            .x-trends h2 {{ border-color: #000000; }} /* 黑 (X) */
            .yt-trends h2 {{ border-color: #c4302b; }} /* 红 (YouTube) */
            .finance h2 {{ border-color: #3498db; }}  /* 蓝 */

            ul {{ padding: 0; margin: 0; list-style: none; }}
            li {{ padding: 6px 0; border-bottom: 1px dashed #f0f0f0; display: flex; align-items: baseline; }}
            li:last-child {{ border-bottom: none; }}
            
            .date {{ color: #bdc3c7; margin-right: 10px; min-width: 55px; text-align: right; font-family: monospace; flex-shrink: 0; font-size: 0.9em; }}
            a {{ text-decoration: none; color: var(--link); transition: color 0.2s; }}
            a:hover {{ color: #3498db; }}
            
            /* Finance Grid */
            .finance-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
            .f-item {{ text-align: center; background: #fafafa; padding: 8px; border-radius: 6px; }}
            .f-name {{ font-size: 0.8em; color: #95a5a6; }}
            .f-price {{ font-weight: bold; font-size: 1.1em; margin: 2px 0; font-family: monospace; }}
            
            @media (max-width: 768px) {{ 
                .grid {{ grid-template-columns: 1fr; }} 
                .finance-grid {{ grid-template-columns: repeat(2, 1fr); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🚀 Geek Dashboard</h1>
                <div class="time">{now}</div>
            </header>
            
            <div class="grid">
                <div class="card hackread">
                    <h2>🔥 HackRead</h2>
                    <ul>{hackread_html}</ul>
                </div>

                <div class="card thn">
                    <h2>🟢 The Hacker News</h2>
                    <ul>{thn_html}</ul>
                </div>

                <div class="card hn">
                    <h2>🍊 Hacker News (YC)</h2>
                    <ul>{hn_html}</ul>
                </div>


            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(">>> index.html 生成完毕！")

# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    print("=== 开始任务 ===")
    
    hackread = get_hackread()
    thn = get_thehackernews()
    hn = get_hacker_news()
    #x_data = get_x_trends()     # 新增
    #yt_data = get_youtube_trends() # 新增
    #fin = get_finance()
    
    generate_html(hackread, thn, hn, x_data, yt_data, fin)
    
    print("=== 完成 ===")