# -*- coding: utf-8 -*-
import requests
import feedparser
import yfinance as yf
import datetime
import time

# =============================================================================
# 1. HackRead (RSS) - 保持不变
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
    except Exception as e:
        print(f"HackRead Error: {e}")
        news_list.append({"title": "HackRead 获取失败", "link": "#", "date": "Err"})
    return news_list

# =============================================================================
# 2. [新替换] The Hacker News (RSS) - 替代 SC World
#    源地址: https://feeds.feedburner.com/TheHackersNews
# =============================================================================
def get_thehackernews():
    news_list = []
    print(">>> 正在获取 The Hacker News...")
    try:
        # 使用 feedparser 解析 RSS，速度快且稳定
        feed = feedparser.parse("https://feeds.feedburner.com/TheHackersNews")
        
        for entry in feed.entries[:8]:
            # 处理日期
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
        print(f"THN Error: {e}")
        news_list.append({"title": "The Hacker News 获取失败", "link": "#", "date": "Err"})
    return news_list

# =============================================================================
# 3. Hacker News (API) - 极客标配
# =============================================================================
def get_hacker_news():
    news = []
    print(">>> 正在获取 Hacker News (YCombinator)...")
    try:
        # 获取前 8 个热门 Stories ID
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
# 4. 最新 CVE 漏洞 (API)
# =============================================================================
def get_cve_alerts():
    cve_list = []
    print(">>> 正在获取最新 CVE...")
    try:
        # 使用 circl.lu 的公共 API
        r = requests.get("https://cve.circl.lu/api/last", timeout=10)
        for item in r.json()[:5]:
            cve_list.append({
                "id": item.get('id'),
                # 限制描述长度，防止破坏布局
                "desc": item.get('summary', '暂无描述')[:65] + "...",
                "link": f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={item.get('id')}"
            })
    except:
        cve_list.append({"id": "Error", "desc": "CVE API 连接失败", "link": "#"})
    return cve_list

# =============================================================================
# 5. 金融数据 (Yahoo API)
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
                    color = "#e74c3c" if pct > 0 else "#2ecc71" # 红涨绿跌
                
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
def generate_html(hackread, thn, hn, cve, finance):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 列表 HTML 生成
    hackread_html = "".join([f'<li><span class="date">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in hackread])
    thn_html = "".join([f'<li><span class="date" style="color:#1abc9c;">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in thn])
    hn_html = "".join([f'<li><span class="date" style="color:#f39c12;font-weight:bold;">{n["score"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in hn])
    
    # CVE 卡片 HTML
    cve_html = "".join([f'<div class="cve-item"><a href="{c["link"]}" target="_blank" class="cve-id">{c["id"]}</a><p class="cve-desc">{c["desc"]}</p></div>' for c in cve])
    
    # 金融卡片 HTML
    finance_html = "".join([f'<div class="f-item"><div class="f-name">{f["name"]}</div><div class="f-price">{f["price"]}</div><div class="f-change" style="color:{f["color"]}">{f["change"]}</div></div>' for f in finance])

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>InfoSec Dashboard</title>
        <style>
            :root {{ --bg: #f4f6f8; --card: #ffffff; --text: #2c3e50; --link: #34495e; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; font-size: 13px; }}
            
            .container {{ max-width: 1200px; margin: 0 auto; }}
            
            header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px; border-bottom: 2px solid #e1e4e8; padding-bottom: 10px; }}
            h1 {{ margin: 0; font-size: 1.5em; color: #34495e; letter-spacing: -0.5px; }}
            .time {{ color: #95a5a6; font-family: monospace; }}
            
            /* 响应式网格 */
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px; }}
            
            .card {{ background: var(--card); padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); border: 1px solid #e1e4e8; }}
            .card h2 {{ margin: 0 0 12px 0; font-size: 1.1em; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; color: #2c3e50; }}
            
            /* 板块颜色条 */
            .hackread h2 {{ border-color: #e74c3c; }} /* 红 */
            .thn h2 {{ border-color: #1abc9c; }}      /* 青绿 */
            .hn h2 {{ border-color: #f39c12; }}       /* 橙 */
            .cve h2 {{ border-color: #9b59b6; }}      /* 紫 */
            .finance h2 {{ border-color: #3498db; }}  /* 蓝 */

            ul {{ padding: 0; margin: 0; list-style: none; }}
            li {{ padding: 6px 0; border-bottom: 1px dashed #f0f0f0; display: flex; align-items: baseline; }}
            li:last-child {{ border-bottom: none; }}
            
            .date {{ color: #bdc3c7; margin-right: 10px; min-width: 45px; text-align: right; font-family: monospace; flex-shrink: 0; }}
            a {{ text-decoration: none; color: var(--link); transition: color 0.2s; }}
            a:hover {{ color: #3498db; }}
            
            /* CVE */
            .cve-item {{ margin-bottom: 8px; border-bottom: 1px solid #f9f9f9; padding-bottom: 8px; }}
            .cve-id {{ color: #c0392b; font-weight: bold; font-family: monospace; font-size: 1.05em; }}
            .cve-desc {{ margin: 2px 0 0 0; color: #7f8c8d; font-size: 0.9em; line-height: 1.4; }}
            
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
                <h1>🛡️ Security Dashboard</h1>
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
                
                <div class="card cve">
                    <h2>🚨 Latest CVE</h2>
                    {cve_html}
                </div>

                <div class="card finance" style="grid-column: 1 / -1;">
                    <h2>💰 Global Markets</h2>
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
    print("=== 开始任务 ===")
    
    # 抓取数据
    hackread_data = get_hackread()
    thn_data = get_thehackernews() # 新增
    hn_data = get_hacker_news()
    cve_data = get_cve_alerts()
    finance_data = get_finance()
    
    # 生成 HTML
    generate_html(hackread_data, thn_data, hn_data, cve_data, finance_data)
    
    print("=== 任务完成 ===")