# -*- coding: utf-8 -*-
import requests
import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
import datetime
import os

# -----------------------------------------------------------------------------
# 1. 科技新闻 (36Kr RSS)
# -----------------------------------------------------------------------------
def get_news():
    news_list = []
    try:
        rss_url = "https://36kr.com/feed"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:10]:
            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "date": entry.published[:10]
            })
    except Exception as e:
        print(f"News Error: {e}")
        news_list.append({"title": "36Kr 抓取失败", "link": "#", "date": ""})
    return news_list

# -----------------------------------------------------------------------------
# 2. GitHub Python 热榜
# -----------------------------------------------------------------------------
def get_github_trending():
    projects = []
    try:
        url = "https://github.com/trending/python?since=daily"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        rows = soup.select('article.Box-row')
        for row in rows[:8]:
            title_tag = row.select_one('h2 a')
            if title_tag:
                title = title_tag.text.strip().replace("\n", "").replace(" ", "")
                link = "https://github.com" + title_tag['href']
            else:
                continue

            desc_tag = row.select_one('p')
            desc = desc_tag.text.strip() if desc_tag else "暂无描述"
            
            star_tag = row.select_one('span.d-inline-block.float-sm-right')
            stars = star_tag.text.strip().split()[0] if star_tag else "0"
            
            projects.append({
                "title": title,
                "link": link,
                "desc": desc,
                "stars": stars
            })
    except Exception as e:
        print(f"GitHub Error: {e}")
        projects.append({"title": "GitHub 抓取失败", "link": "#", "desc": str(e), "stars": "0"})
    return projects

# -----------------------------------------------------------------------------
# 3. 金融数据 (Stocks/Crypto)
# -----------------------------------------------------------------------------
def get_finance():
    data = []
    symbols = [
        {"name": "上证指数", "code": "000001.SS"},
        {"name": "纳斯达克", "code": "^IXIC"},
        {"name": "比特币", "code": "BTC-USD"},
        {"name": "英伟达", "code": "NVDA"}
    ]
    
    for item in symbols:
        try:
            ticker = yf.Ticker(item["code"])
            hist = ticker.history(period="2d")
            if len(hist) >= 1:
                price = hist['Close'].iloc[-1]
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[0]
                    change = (price - prev_close) / prev_close * 100
                    change_str = f"{change:+.2f}%"
                    # 红色涨，绿色跌
                    color = "#d63031" if change > 0 else "#00b894"
                else:
                    change_str = "-"
                    color = "black"
                
                data.append({
                    "name": item["name"],
                    "price": f"{price:.2f}",
                    "change": change_str,
                    "color": color
                })
        except Exception as e:
            print(f"Finance Error {item['name']}: {e}")
    return data

# -----------------------------------------------------------------------------
# 4. Hacker News (Global Tech)
# -----------------------------------------------------------------------------
def get_hacker_news():
    news_list = []
    try:
        # 增加超时设置，防止卡住
        ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:8]
        for item_id in ids:
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=5).json()
            if item:
                title = item.get('title', 'No Title')
                url = item.get('url', f"https://news.ycombinator.com/item?id={item_id}")
                score = item.get('score', 0)
                news_list.append({
                    "title": title,
                    "link": url,
                    "score": f"🔥{score}"
                })
    except Exception as e:
        print(f"HN Error: {e}")
        news_list.append({"title": "Hacker News 抓取失败", "link": "#", "score": ""})
    return news_list

# -----------------------------------------------------------------------------
# 5. V2EX Hot (China Tech)
# -----------------------------------------------------------------------------
def get_v2ex_hot():
    topics = []
    try:
        url = "https://www.v2ex.com/api/topics/hot.json"
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        resp = requests.get(url, headers=headers, timeout=10).json()
        
        for item in resp[:8]:
            topics.append({
                "title": item['title'],
                "link": item['url'],
                "replies": f"💬{item['replies']}"
            })
    except Exception as e:
        print(f"V2EX Error: {e}")
        topics.append({"title": "V2EX 抓取失败", "link": "#", "replies": ""})
    return topics

# -----------------------------------------------------------------------------
# 生成 HTML
# -----------------------------------------------------------------------------
def generate_html(news, projects, finance, hacker_news, v2ex_data):
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + datetime.timedelta(hours=8)
    date_str = beijing_time.strftime("%Y-%m-%d %H:%M")

    # 1. 36Kr HTML
    news_html = "".join([f'<li><span class="date">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in news])
    
    # 2. Hacker News HTML
    hn_html = "".join([f'<li><span class="date" style="color:#ff6600; font-weight:bold;">{n["score"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in hacker_news])
    
    # 3. V2EX HTML
    v2ex_html = "".join([f'<li><span class="date">{n["replies"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in v2ex_data])

    # 4. GitHub HTML
    projects_html = "".join([f'''
        <div class="project-item">
            <div class="p-title"><a href="{p["link"]}" target="_blank">{p["title"]}</a> <span class="stars">⭐{p["stars"]}</span></div>
            <div class="p-desc">{p["desc"]}</div>
        </div>''' for p in projects])
        
    # 5. Finance HTML
    finance_html = "".join([f'''
        <div class="finance-item">
            <div class="f-name">{f["name"]}</div>
            <div class="f-price">{f["price"]}</div>
            <div class="f-change" style="color:{f["color"]}">{f["change"]}</div>
        </div>''' for f in finance])

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>我的极客仪表盘</title>
        <style>
            :root {{ --bg: #f4f6f8; --card-bg: #ffffff; --text: #333; --accent: #007bff; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
            .container {{ max-width: 1400px; margin: 0 auto; }} /* 宽度加大 */
            header {{ text-align: center; margin-bottom: 30px; }}
            h1 {{ margin: 0; font-size: 2em; color: #2c3e50; }}
            .time {{ color: #7f8c8d; font-size: 0.9em; margin-top: 5px; }}
            
            /* Responsive Grid */
            .dashboard {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }}
            
            .card {{ background: var(--card-bg); border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 12px rgba(0,0,0,0.1); }}
            .card h2 {{ margin-top: 0; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; font-size: 1.2em; color: #007bff; display: flex; align-items: center; justify-content: space-between;}}
            
            ul.news-list {{ list-style: none; padding: 0; }}
            ul.news-list li {{ padding: 8px 0; border-bottom: 1px dashed #eee; display: flex; align-items: baseline; font-size: 0.95em; }}
            ul.news-list li:last-child {{ border-bottom: none; }}
            
            /* 日期/热度标签样式 */
            .date {{ font-size: 0.85em; color: #999; margin-right: 10px; min-width: 65px; text-align: right; flex-shrink: 0; }}
            
            a {{ text-decoration: none; color: #333; transition: color 0.2s; line-height: 1.4; }}
            a:hover {{ color: var(--accent); }}
            
            .project-item {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #f9f9f9; }}
            .p-title {{ font-weight: bold; font-size: 1.05em; }}
            .p-desc {{ font-size: 0.9em; color: #666; margin-top: 4px; line-height: 1.4; }}
            .stars {{ float: right; font-size: 0.8em; color: #f1c40f; background: #fffbe6; padding: 2px 6px; border-radius: 4px; }}
            
            .finance-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }}
            .finance-item {{ text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px; }}
            .f-name {{ font-size: 0.9em; color: #666; }}
            .f-price {{ font-size: 1.2em; font-weight: bold; margin: 5px 0; }}
            .f-change {{ font-size: 0.9em; font-weight: bold; }}
            
            @media (max-width: 768px) {{ .dashboard {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🚀 Daily Dashboard</h1>
                <p class="time">更新于: {date_str} (Beijing Time)</p>
            </header>
            
            <div class="dashboard">
                <div class="card">
                    <h2>📰 36Kr 科技</h2>
                    <ul class="news-list">
                        {news_html}
                    </ul>
                </div>

                <div class="card">
                    <h2>🍊 Hacker News</h2>
                    <ul class="news-list">
                        {hn_html}
                    </ul>
                </div>

                <div class="card">
                    <h2>⚡ V2EX 极客</h2>
                    <ul class="news-list">
                        {v2ex_html}
                    </ul>
                </div>
                
                <div class="card">
                    <h2>🐍 GitHub Trending</h2>
                    {projects_html}
                </div>
                
                <div class="card">
                    <h2>💰 市场指数</h2>
                    <div class="finance-grid">
                        {finance_html}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("Starting job...")
    
    print("Fetching News (36Kr)...")
    news_data = get_news()
    
    print("Fetching Hacker News...")
    hn_data = get_hacker_news()

    print("Fetching V2EX...")
    v2ex_data = get_v2ex_hot()

    print("Fetching GitHub Trending...")
    github_data = get_github_trending()
    
    print("Fetching Finance Data...")
    finance_data = get_finance()
    
    print("Generating HTML...")
    generate_html(news_data, github_data, finance_data, hn_data, v2ex_data)
    
    print("Done! index.html updated.")