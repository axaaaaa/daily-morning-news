# -*- coding: utf-8 -*-
import requests
import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
import datetime
import os

# --- 1. 获取科技新闻 (基于 36Kr RSS) ---
def get_news():
    news_list = []
    try:
        # 使用 36Kr 的 RSS 源
        rss_url = "https://36kr.com/feed"
        feed = feedparser.parse(rss_url)
        # 只取前 10 条
        for entry in feed.entries[:10]:
            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "date": entry.published[:10] # 截取日期
            })
    except Exception as e:
        print(f"News Error: {e}")
        news_list.append({"title": "新闻抓取失败，请检查网络", "link": "#", "date": ""})
    return news_list

# --- 2. 获取 GitHub Python 热榜 (爬虫) ---
def get_github_trending():
    projects = []
    try:
        url = "https://github.com/trending/python?since=daily"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 抓取项目行
        rows = soup.select('article.Box-row')
        for row in rows[:8]: # 只取前 8 个
            # 获取项目名
            title = row.select_one('h2 a').text.strip().replace("\n", "").replace(" ", "")
            # 获取链接
            link = "https://github.com" + row.select_one('h2 a')['href']
            # 获取描述 (有的项目没有描述)
            desc_tag = row.select_one('p')
            desc = desc_tag.text.strip() if desc_tag else "暂无描述"
            # 获取 Star 数
            stars = row.select_one('span.d-inline-block.float-sm-right').text.strip().split()[0]
            
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

# --- 3. 获取金融数据 (上证、纳指、BTC) ---
def get_finance():
    data = []
    # 代码: 上证指数(000001.SS), 纳斯达克(^IXIC), 比特币(BTC-USD), 苹果(AAPL)
    symbols = [
        {"name": "上证指数", "code": "000001.SS"},
        {"name": "纳斯达克", "code": "^IXIC"},
        {"name": "比特币", "code": "BTC-USD"},
        {"name": "英伟达", "code": "NVDA"}
    ]
    
    for item in symbols:
        try:
            ticker = yf.Ticker(item["code"])
            # 获取今日行情 (fast approach)
            hist = ticker.history(period="2d")
            if len(hist) >= 1:
                price = hist['Close'].iloc[-1]
                # 计算简单的涨跌 (如果有2天数据)
                if len(hist) >= 2:
                    prev_close = hist['Close'].iloc[0]
                    change = (price - prev_close) / prev_close * 100
                    change_str = f"{change:+.2f}%"
                    color = "red" if change > 0 else "green" # A股红涨绿跌，美股相反，这里统一用红涨
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

# --- 4. 生成网页 ---
def generate_html(news, projects, finance):
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + datetime.timedelta(hours=8)
    date_str = beijing_time.strftime("%Y-%m-%d %H:%M")

    # 构建 HTML 列表
    news_html = "".join([f'<li><span class="date">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in news])
    
    projects_html = "".join([f'''
        <div class="project-item">
            <div class="p-title"><a href="{p["link"]}" target="_blank">{p["title"]}</a> <span class="stars">⭐{p["stars"]}</span></div>
            <div class="p-desc">{p["desc"]}</div>
        </div>''' for p in projects])
        
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
            .container {{ max-width: 1200px; margin: 0 auto; }}
            header {{ text-align: center; margin-bottom: 30px; }}
            h1 {{ margin: 0; font-size: 2em; color: #2c3e50; }}
            .time {{ color: #7f8c8d; font-size: 0.9em; margin-top: 5px; }}
            
            /* Grid Layout */
            .dashboard {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }}
            
            /* Card Styles */
            .card {{ background: var(--card-bg); border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            .card h2 {{ margin-top: 0; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; font-size: 1.2em; color: #007bff; }}
            
            /* News List */
            ul.news-list {{ list-style: none; padding: 0; }}
            ul.news-list li {{ padding: 10px 0; border-bottom: 1px dashed #eee; display: flex; align-items: baseline; }}
            ul.news-list li:last-child {{ border-bottom: none; }}
            .date {{ font-size: 0.8em; color: #999; margin-right: 10px; min-width: 50px; }}
            a {{ text-decoration: none; color: #333; transition: color 0.2s; }}
            a:hover {{ color: var(--accent); }}
            
            /* GitHub Projects */
            .project-item {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #f9f9f9; }}
            .p-title {{ font-weight: bold; font-size: 1.05em; }}
            .p-desc {{ font-size: 0.9em; color: #666; margin-top: 4px; line-height: 1.4; }}
            .stars {{ float: right; font-size: 0.8em; color: #f1c40f; background: #fffbe6; padding: 2px 6px; border-radius: 4px; }}
            
            /* Finance */
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
                <p class="time">更新于: {date_str}</p>
            </header>
            
            <div class="dashboard">
                <div class="card">
                    <h2>📰 科技要闻 (36Kr)</h2>
                    <ul class="news-list">
                        {news_html}
                    </ul>
                </div>
                
                <div class="card">
                    <h2>🔥 GitHub Python 热榜</h2>
                    {projects_html}
                </div>
                
                <div class="card">
                    <h2>💰 市场风向标</h2>
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

if __name__ == "__main__":
    print("Starting job...")
    
    print("Fetching News...")
    news_data = get_news()
    
    print("Fetching GitHub Trending...")
    github_data = get_github_trending()
    
    print("Fetching Finance Data...")
    finance_data = get_finance()
    
    print("Generating HTML...")
    generate_html(news_data, github_data, finance_data)
    
    print("Done!")
