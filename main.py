# -*- coding: utf-8 -*-
import requests
import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
import datetime
import time
import random

# 设置通用的浏览器伪装头，防止被 SC World 拦截
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

# =============================================================================
# 1. [新增] HackRead (使用 RSS)
# =============================================================================
def get_hackread():
    news_list = []
    print(">>> 正在获取 HackRead...")
    try:
        # HackRead 官方 RSS
        feed = feedparser.parse("https://hackread.com/feed/")
        
        for entry in feed.entries[:8]:
            # 格式化日期
            pub_date = "Today"
            if hasattr(entry, 'published_parsed'):
                dt = datetime.datetime(*entry.published_parsed[:6])
                pub_date = dt.strftime("%m-%d")
            
            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "date": pub_date
            })
    except Exception as e:
        print(f"HackRead Error: {e}")
        news_list.append({"title": "HackRead 获取失败", "link": "#", "date": "Err"})
    return news_list

# =============================================================================
# 2. [新增] SC World - Security Weekly (HTML 爬虫)
# =============================================================================
def get_scworld_weekly():
    news_list = []
    print(">>> 正在获取 SC World (Security Weekly)...")
    target_url = "https://www.scworld.com/security-weekly"
    
    try:
        r = requests.get(target_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # SC World 的结构比较现代，通常文章标题在 h2 或 h3 中
        # 我们查找包含链接的标题
        articles = soup.find_all(['h2', 'h3'], limit=15)
        
        count = 0
        for art in articles:
            link_tag = art.find('a')
            if link_tag and link_tag.get('href'):
                title = link_tag.get_text().strip()
                href = link_tag.get('href')
                
                # 补全相对链接
                if href.startswith('/'):
                    href = "https://www.scworld.com" + href
                
                # 过滤掉非文章的短标题
                if len(title) > 10:
                    news_list.append({
                        "title": title,
                        "link": href,
                        "date": "New" # 网页版抓取很难精准解析日期，统一标记
                    })
                    count += 1
                    if count >= 8: break
                    
        if not news_list:
            # 如果抓取为空（可能是结构变了），尝试 fallback 到主 RSS
            print("   -> HTML 解析为空，尝试 RSS 备用方案...")
            return get_scworld_rss()
            
    except Exception as e:
        print(f"SC World Error: {e}")
        news_list.append({"title": "SC World 连接失败", "link": "#", "date": "Err"})
    
    return news_list

def get_scworld_rss():
    # 备用方案：抓取 SC World 主 RSS
    data = []
    try:
        feed = feedparser.parse("https://www.scworld.com/rss")
        for entry in feed.entries[:8]:
            data.append({
                "title": entry.title,
                "link": entry.link,
                "date": "RSS"
            })
    except:
        pass
    return data

# =============================================================================
# 3. Hacker News (API) - 极客标配
# =============================================================================
def get_hacker_news():
    news = []
    print(">>> 正在获取 Hacker News...")
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
        news.append({"title": "HN 获取失败", "link": "#", "score": "Err"})
    return news

# =============================================================================
# 4. 最新 CVE 漏洞 (API)
# =============================================================================
def get_cve_alerts():
    cve_list = []
    print(">>> 正在获取最新 CVE...")
    try:
        r = requests.get("https://cve.circl.lu/api/last", timeout=10)
        for item in r.json()[:5]:
            cve_list.append({
                "id": item.get('id'),
                "desc": item.get('summary', '暂无描述')[:60] + "...",
                "link": f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={item.get('id')}"
            })
    except:
        cve_list.append({"id": "Error", "desc": "API连接失败", "link": "#"})
    return cve_list

# =============================================================================
# 5. 金融数据 (Yahoo)
# =============================================================================
def get_finance():
    data = []
    print(">>> 正在获取金融数据...")
    symbols = [
        {"name": "BTC", "code": "BTC-USD"},
        {"name": "ETH", "code": "ETH-USD"},
        {"name": "NVDA", "code": "NVDA"},
        {"name": "NASDAQ", "code": "^IXIC"}
    ]
    for item in symbols:
        try:
            ticker = yf.Ticker(item["code"])
            hist = ticker.history(period="2d")
            if len(hist) > 0:
                price = hist['Close'].iloc[-1]
                change_str, color = "-", "#333"
                if len(hist) > 1:
                    prev = hist['Close'].iloc[0]
                    pct = ((price - prev) / prev) * 100
                    change_str = f"{pct:+.2f}%"
                    color = "#e74c3c" if pct > 0 else "#2ecc71"
                
                data.append({
                    "name": item["name"],
                    "price": f"{price:,.1f}",
                    "change": change_str,
                    "color": color
                })
        except:
            pass
    return data

# =============================================================================
# 生成 HTML
# =============================================================================
def generate_html(hackread, scworld, hn, cve, finance):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    hackread_html = "".join([f'<li><span class="date">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in hackread])
    scworld_html = "".join([f'<li><span class="date" style="color:#3498db;">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in scworld])
    hn_html = "".join([f'<li><span class="date" style="color:#f39c12;font-weight:bold;">{n["score"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in hn])
    cve_html = "".join([f'<div class="cve-item"><a href="{c["link"]}" target="_blank" class="cve-id">{c["id"]}</a><p class="cve-desc">{c["desc"]}</p></div>' for c in cve])
    finance_html = "".join([f'<div class="f-item"><div class="f-name">{f["name"]}</div><div class="f-price">{f["price"]}</div><div class="f-change" style="color:{f["color"]}">{f["change"]}</div></div>' for f in finance])

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>InfoSec Dashboard</title>
        <style>
            :root {{ --bg: #f0f2f5; --card: #ffffff; --text: #2c3e50; --link: #2c3e50; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; font-size: 13px; }}
            
            .container {{ max-width: 1200px; margin: 0 auto; }}
            
            header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px; border-bottom: 2px solid #e1e4e8; padding-bottom: 10px; }}
            h1 {{ margin: 0; font-size: 1.5em; color: #34495e; }}
            .time {{ color: #7f8c8d; font-family: monospace; }}
            
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px; }}
            
            .card {{ background: var(--card); padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); border: 1px solid #e1e4e8; }}
            .card h2 {{ margin: 0 0 12px 0; font-size: 1.1em; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; color: #2c3e50; }}
            
            /* 强调色 */
            .hackread h2 {{ border-color: #e74c3c; }} /* 红色系 */
            .scworld h2 {{ border-color: #3498db; }} /* 蓝色系 */
            .hn h2 {{ border-color: #f39c12; }} /* 橙色系 */
            .cve h2 {{ border-color: #9b59b6; }} /* 紫色系 */
            .finance h2 {{ border-color: #27ae60; }} /* 绿色系 */

            ul {{ padding: 0; margin: 0; list-style: none; }}
            li {{ padding: 6px 0; border-bottom: 1px dashed #f0f0f0; display: flex; align-items: baseline; }}
            li:last-child {{ border-bottom: none; }}
            
            .date {{ color: #bdc3c7; margin-right: 10px; min-width: 45px; text-align: right; font-family: monospace; flex-shrink: 0; }}
            a {{ text-decoration: none; color: var(--link); transition: color 0.2s; }}
            a:hover {{ color: #2980b9; }}
            
            /* CVE */
            .cve-item {{ margin-bottom: 8px; border-bottom: 1px solid #f9f9f9; padding-bottom: 8px; }}
            .cve-id {{ color: #c0392b; font-weight: bold; font-family: monospace; font-size: 1.05em; }}
            .cve-desc {{ margin: 2px 0 0 0; color: #7f8c8d; font-size: 0.9em; }}
            
            /* Finance */
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
                <h1>🛡️ InfoSec Dashboard</h1>
                <div class="time">{now}</div>
            </header>
            
            <div class="grid">
                <div class="card hackread">
                    <h2>🔥 HackRead</h2>
                    <ul>{hackread_html}</ul>
                </div>

                <div class="card scworld">
                    <h2>🌐 SC World Weekly</h2>
                    <ul>{scworld_html}</ul>
                </div>

                <div class="card hn">
                    <h2>🍊 Hacker News</h2>
                    <ul>{hn_html}</ul>
                </div>
                
                <div class="card cve">
                    <h2>🚨 Latest CVE</h2>
                    {cve_html}
                </div>

                <div class="card finance" style="grid-column: 1 / -1;">
                    <h2>💰 Markets</h2>
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
    print(">>> index.html 生成完毕！")

if __name__ == "__main__":
    print("=== 开始抓取安全资讯 ===")
    
    hackread_data = get_hackread()
    scworld_data = get_scworld_weekly()
    hn_data = get_hacker_news()
    cve_data = get_cve_alerts()
    finance_data = get_finance()
    
    generate_html(hackread_data, scworld_data, hn_data, cve_data, finance_data)
    
    print("=== 任务完成 ===")