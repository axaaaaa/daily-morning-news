# -*- coding: utf-8 -*-
import requests
import feedparser
import yfinance as yf
import datetime
import time

# =============================================================================
# 1. [修复] 聚合科技新闻 (ReadHub API)
#    直接调用接口，不再抓取网页，解决“不显示”的问题
# =============================================================================
def get_readhub():
    news_list = []
    print(">>> 正在获取 ReadHub...")
    try:
        # type=news 代表科技动态, pageSize=10 代表取10条
        api_url = "https://api.readhub.cn/topic?type=news&pageSize=10"
        r = requests.get(api_url, timeout=10)
        
        if r.status_code == 200:
            items = r.json().get('data', [])
            for item in items:
                # 原始时间格式: "2023-12-10T10:30:00.000Z" -> 截取 "10:30"
                time_str = item['publishDate'][11:16] 
                news_list.append({
                    "title": item['title'],
                    "link": f"https://readhub.cn/topic/{item['id']}",
                    "date": time_str
                })
        else:
            news_list.append({"title": "ReadHub 接口返回错误", "link": "#", "date": "Err"})
            
    except Exception as e:
        print(f"ReadHub Error: {e}")
        news_list.append({"title": "ReadHub 连接失败", "link": "#", "date": "Err"})
    return news_list

# =============================================================================
# 2. [修复] 网络安全 (FreeBuf RSS)
#    改用 RSS 解析，解决“显示不对/错乱”的问题
# =============================================================================
def get_security_news():
    news_list = []
    print(">>> 正在获取 FreeBuf 安全情报...")
    try:
        # FreeBuf 的 RSS 源非常稳定
        feed = feedparser.parse("https://www.freebuf.com/feed")
        
        if not feed.entries:
            # 如果 FreeBuf 挂了，备用方案：Solidot
            feed = feedparser.parse("https://solidot.org/index.rss")
            
        for entry in feed.entries[:8]:
            # 处理日期，只留 月-日
            pub_date = "Today"
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime.datetime(*entry.published_parsed[:6])
                pub_date = dt.strftime("%m-%d")
            
            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "date": pub_date
            })
    except Exception as e:
        print(f"Security Error: {e}")
        news_list.append({"title": "安全情报获取失败", "link": "#", "date": "Err"})
    return news_list

# =============================================================================
# 3. 最新 CVE 漏洞 (API)
# =============================================================================
def get_cve_alerts():
    cve_list = []
    print(">>> 正在获取最新 CVE...")
    try:
        r = requests.get("https://cve.circl.lu/api/last", timeout=10)
        if r.status_code == 200:
            for item in r.json()[:5]:
                cve_list.append({
                    "id": item.get('id'),
                    # 描述过长则截断
                    "desc": item.get('summary', '无描述')[:55] + "...",
                    "link": f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={item.get('id')}"
                })
    except:
        cve_list.append({"id": "Error", "desc": "CVE API 连接失败", "link": "#"})
    return cve_list

# =============================================================================
# 4. Hacker News (API)
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
# 5. 金融数据 (Yahoo)
# =============================================================================
def get_finance():
    data = []
    print(">>> 正在获取金融数据...")
    # 可以自定义你想看的代码
    symbols = [
        {"name": "BTC", "code": "BTC-USD"},
        {"name": "ETH", "code": "ETH-USD"},
        {"name": "NVDA", "code": "NVDA"},
        {"name": "纳指", "code": "^IXIC"}
    ]
    for item in symbols:
        try:
            ticker = yf.Ticker(item["code"])
            # 获取最近2天数据以计算涨跌
            hist = ticker.history(period="2d")
            if len(hist) > 0:
                price = hist['Close'].iloc[-1]
                # 计算涨跌幅
                change_str = "-"
                color = "#333"
                if len(hist) > 1:
                    prev = hist['Close'].iloc[0]
                    pct = ((price - prev) / prev) * 100
                    change_str = f"{pct:+.2f}%"
                    color = "#e74c3c" if pct > 0 else "#2ecc71" # 红涨绿跌
                
                data.append({
                    "name": item["name"],
                    "price": f"{price:,.1f}", # 千分位
                    "change": change_str,
                    "color": color
                })
        except:
            pass
    return data

# =============================================================================
# 生成 HTML (Compact Design)
# =============================================================================
def generate_html(readhub, security, cve, hn, finance):
    # 获取当前时间
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 拼接 HTML 列表
    readhub_html = "".join([f'<li><span class="date">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in readhub])
    security_html = "".join([f'<li><span class="date" style="color:#27ae60;">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in security])
    hn_html = "".join([f'<li><span class="date" style="color:#f39c12;font-weight:bold;">{n["score"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in hn])
    cve_html = "".join([f'<div class="cve-item"><a href="{c["link"]}" target="_blank" class="cve-id">{c["id"]}</a><p class="cve-desc">{c["desc"]}</p></div>' for c in cve])
    finance_html = "".join([f'<div class="f-item"><div class="f-name">{f["name"]}</div><div class="f-price">{f["price"]}</div><div class="f-change" style="color:{f["color"]}">{f["change"]}</div></div>' for f in finance])

    # 完整的 HTML 模板
    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Geek Dashboard</title>
        <style>
            :root {{ --bg: #f4f7f6; --card: #ffffff; --text: #2c3e50; --link: #34495e; --hover: #3498db; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; font-size: 13px; }}
            
            .container {{ max-width: 1100px; margin: 0 auto; }}
            
            header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px; border-bottom: 2px solid #e1e4e8; padding-bottom: 10px; }}
            h1 {{ margin: 0; font-size: 1.5em; color: #2c3e50; letter-spacing: -0.5px; }}
            .time {{ color: #7f8c8d; font-family: monospace; }}
            
            /* 紧凑网格布局 */
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px; }}
            
            .card {{ background: var(--card); padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); border: 1px solid #eaeaea; }}
            .card h2 {{ margin: 0 0 12px 0; font-size: 1.1em; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; display: flex; align-items: center; justify-content: space-between; color: #2c3e50; }}
            
            /* 强调色条 */
            .readhub h2 {{ border-color: #3498db; }}
            .security h2 {{ border-color: #2ecc71; }}
            .hn h2 {{ border-color: #f39c12; }}
            .cve h2 {{ border-color: #e74c3c; }}
            .finance h2 {{ border-color: #9b59b6; }}

            ul {{ padding: 0; margin: 0; list-style: none; }}
            li {{ padding: 6px 0; border-bottom: 1px dashed #f0f0f0; display: flex; align-items: baseline; }}
            li:last-child {{ border-bottom: none; }}
            
            .date {{ color: #bdc3c7; margin-right: 10px; min-width: 45px; text-align: right; font-family: monospace; flex-shrink: 0; }}
            
            a {{ text-decoration: none; color: var(--link); transition: color 0.2s; }}
            a:hover {{ color: var(--hover); }}
            
            /* CVE 特殊样式 */
            .cve-item {{ margin-bottom: 8px; border-bottom: 1px solid #f9f9f9; padding-bottom: 8px; }}
            .cve-id {{ color: #e74c3c; font-weight: bold; font-family: monospace; font-size: 1.05em; }}
            .cve-desc {{ margin: 2px 0 0 0; color: #7f8c8d; line-height: 1.4; font-size: 0.9em; }}
            
            /* 金融横条样式 */
            .finance-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
            .f-item {{ text-align: center; background: #fafafa; padding: 8px; border-radius: 6px; }}
            .f-name {{ font-size: 0.8em; color: #95a5a6; }}
            .f-price {{ font-weight: bold; font-size: 1.1em; margin: 2px 0; font-family: monospace; }}
            .f-change {{ font-size: 0.85em; font-weight: bold; }}

            @media (max-width: 700px) {{ 
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
                <div class="card readhub">
                    <h2>📰 ReadHub Tech</h2>
                    <ul>{readhub_html}</ul>
                </div>

                <div class="card security">
                    <h2>🛡️ FreeBuf Security</h2>
                    <ul>{security_html}</ul>
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
                    <h2>💰 Market Overview</h2>
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
        f.write(html_template)
    print(">>> 页面生成完毕: index.html")

# =============================================================================
# 主程序
# =============================================================================
if __name__ == "__main__":
    print("=== 开始任务 ===")
    
    # 获取数据
    rh_data = get_readhub()
    sec_data = get_security_news()
    cve_data = get_cve_alerts()
    hn_data = get_hacker_news()
    fin_data = get_finance()
    
    # 生成页面
    generate_html(rh_data, sec_data, cve_data, hn_data, fin_data)
    
    print("=== 任务结束 ===")