# -*- coding: utf-8 -*-
import requests
import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
import datetime
import os

# =============================================================================
# 1. 聚合科技新闻 (ReadHub) - 替代 36Kr
# =============================================================================
def get_readhub():
    news_list = []
    try:
        # ReadHub 热门话题
        api_url = "https://api.readhub.cn/topic?pageSize=10"
        r = requests.get(api_url, timeout=10)
        if r.status_code == 200:
            items = r.json().get('data', [])
            for item in items:
                # 截取时间 HH:MM
                time_str = item['publishDate'][11:16]
                news_list.append({
                    "title": item['title'],
                    "link": f"https://readhub.cn/topic/{item['id']}",
                    "date": time_str
                })
    except Exception as e:
        print(f"ReadHub Error: {e}")
        news_list.append({"title": "ReadHub 抓取失败", "link": "#", "date": "Err"})
    return news_list

# =============================================================================
# 2. 安全情报 (Solidot + CVE)
# =============================================================================
def get_solidot():
    # 硬核科技/开源/安全新闻
    news_list = []
    try:
        feed = feedparser.parse("https://solidot.org/index.rss")
        for entry in feed.entries[:6]:
            # Solidot 的日期通常比较长，简化一下
            date_pub = entry.published.split('T')[0][5:] if 'T' in entry.published else "Today"
            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "date": date_pub
            })
    except Exception as e:
        print(f"Solidot Error: {e}")
    return news_list

def get_cve_alerts():
    # 获取最新的 CVE 漏洞 (使用 cve.circl.lu API，无需 Key)
    cve_list = []
    try:
        # 获取最近 5 个
        r = requests.get("https://cve.circl.lu/api/last", timeout=10)
        if r.status_code == 200:
            items = r.json()[:5]
            for item in items:
                cve_id = item.get('id', 'Unknown')
                summary = item.get('summary', '暂无描述')
                # 截断描述以适应紧凑布局
                desc = summary[:50] + "..." if len(summary) > 50 else summary
                cve_list.append({
                    "id": cve_id,
                    "desc": desc,
                    "link": f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id}"
                })
    except Exception as e:
        print(f"CVE Error: {e}")
        cve_list.append({"id": "Error", "desc": "无法连接 CVE 数据库", "link": "#"})
    return cve_list

# =============================================================================
# 3. AI 趋势 (Hugging Face Trending)
# =============================================================================
def get_huggingface():
    models = []
    try:
        url = "https://huggingface.co/models?sort=trending"
        r = requests.get(url, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # HuggingFace 的类名经常变，这里尝试抓取 article 标签
        articles = soup.select('article')
        for art in articles[:7]:
            header = art.select_one('header h4')
            if not header: continue
            
            name = header.text.strip()
            link = "https://huggingface.co" + art.select_one('a')['href']
            
            # 尝试获取点赞/下载数 (通常在底部的 svg 旁边)
            # 这里做一个简单的容错处理
            stats_div = art.select_one('div.flex.items-center.mt-2')
            heat = "🔥"
            if stats_div:
                heat = stats_div.get_text(strip=True).replace('\n', ' ')
            
            models.append({
                "name": name,
                "link": link,
                "heat": heat
            })
    except Exception as e:
        print(f"HF Error: {e}")
        models.append({"name": "Fetch Failed", "link": "#", "heat": ""})
    return models

# =============================================================================
# 4. GitHub Python 热榜 (保留)
# =============================================================================
def get_github_trending():
    projects = []
    try:
        url = "https://github.com/trending/python?since=daily"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for row in soup.select('article.Box-row')[:6]:
            title_tag = row.select_one('h2 a')
            if title_tag:
                title = title_tag.text.strip().replace("\n", "").replace(" ", "")
                link = "https://github.com" + title_tag['href']
                
                desc_tag = row.select_one('p')
                desc = desc_tag.text.strip() if desc_tag else ""
                
                star_tag = row.select_one('span.d-inline-block.float-sm-right')
                stars = star_tag.text.strip().split()[0] if star_tag else "0"
                
                projects.append({"title": title, "link": link, "desc": desc, "stars": stars})
    except Exception as e:
        print(f"GitHub Error: {e}")
    return projects

# =============================================================================
# 5. 金融数据 (保留)
# =============================================================================
def get_finance():
    data = []
    symbols = [
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
                    change = (price - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100
                    color = "#d63031" if change > 0 else "#00b894"
                    change_str = f"{change:+.2f}%"
                else:
                    color, change_str = "black", "-"
                data.append({"name": item["name"], "price": f"{price:.2f}", "change": change_str, "color": color})
        except:
            pass
    return data

# =============================================================================
# 生成 HTML (Compact Geek Mode)
# =============================================================================
def generate_html(readhub, solidot, cve, hf, github, finance):
    date_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")

    # 构建 HTML 片段
    readhub_html = "".join([f'<li><span class="date">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in readhub])
    
    solidot_html = "".join([f'<li><span class="date" style="color:#2ecc71;">{n["date"]}</span><a href="{n["link"]}" target="_blank">{n["title"]}</a></li>' for n in solidot])
    
    cve_html = "".join([f'<li style="display:block; border-bottom:1px solid #eee; padding:6px 0;"><div style="display:flex; justify-content:space-between;"><a href="{c["link"]}" target="_blank" style="color:#e74c3c; font-weight:bold; font-family:monospace;">{c["id"]}</a></div><div style="font-size:0.8em; color:#666; margin-top:2px;">{c["desc"]}</div></li>' for c in cve])
    
    hf_html = "".join([f'<li><span class="date" style="color:#f1c40f; font-weight:bold;">{n["heat"][:4]}</span><a href="{n["link"]}" target="_blank">{n["name"]}</a></li>' for n in hf])
    
    github_html = "".join([f'<div class="project-item"><div class="p-title"><a href="{p["link"]}" target="_blank">{p["title"]}</a> <span class="stars">⭐{p["stars"]}</span></div><div class="p-desc">{p["desc"][:50]}...</div></div>' for p in github])
    
    finance_html = "".join([f'<div class="finance-item"><div class="f-name">{f["name"]}</div><div class="f-price">{f["price"]}</div><div class="f-change" style="color:{f["color"]}">{f["change"]}</div></div>' for f in finance])

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Geek Dashboard</title>
        <style>
            :root {{ --bg: #f0f2f5; --card-bg: #ffffff; --text: #2c3e50; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background-color: var(--bg); color: var(--text); margin: 0; padding: 15px; font-size: 13px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            
            header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 15px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
            h1 {{ margin: 0; font-size: 1.4em; color: #34495e; font-weight: 800; letter-spacing: -0.5px; }}
            .time {{ color: #95a5a6; font-family: monospace; font-size: 0.9em; }}
            
            .dashboard {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px; }}
            
            .card {{ background: var(--card-bg); border-radius: 8px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #e1e4e8; }}
            .card:hover {{ box-shadow: 0 4px 6px rgba(0,0,0,0.08); transform: translateY(-1px); transition: all 0.2s; }}
            
            .card h2 {{ margin-top: 0; padding-bottom: 8px; margin-bottom: 10px; font-size: 1.1em; display: flex; align-items: center; border-bottom: 2px solid transparent; }}
            
            /* 各板块颜色定义 */
            .readhub h2 {{ color: #007bff; border-color: #007bff; }}
            .security h2 {{ color: #e74c3c; border-color: #e74c3c; }}
            .ai h2 {{ color: #f39c12; border-color: #f39c12; }}
            .github h2 {{ color: #24292e; border-color: #24292e; }}
            .finance h2 {{ color: #27ae60; border-color: #27ae60; }}

            ul {{ list-style: none; padding: 0; margin: 0; }}
            ul li {{ padding: 6px 0; border-bottom: 1px dashed #eee; display: flex; align-items: baseline; }}
            ul li:last-child {{ border-bottom: none; }}
            
            .date {{ font-family: monospace; color: #999; margin-right: 8px; min-width: 40px; text-align: right; flex-shrink: 0; font-size: 0.9em; }}
            a {{ text-decoration: none; color: #333; transition: color 0.2s; }}
            a:hover {{ color: #0056b3; }}
            
            /* 项目列表样式 */
            .project-item {{ padding: 8px 0; border-bottom: 1px solid #f1f1f1; }}
            .p-title {{ font-weight: 600; font-size: 1em; display: flex; justify-content: space-between; }}
            .p-desc {{ font-size: 0.85em; color: #666; margin-top: 3px; line-height: 1.3; }}
            .stars {{ font-size: 0.8em; background: #fafbfc; border: 1px solid #e1e4e8; padding: 0 5px; border-radius: 4px; }}
            
            /* 金融样式 */
            .finance-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
            .finance-item {{ text-align: center; background: #f8f9fa; padding: 8px; border-radius: 6px; }}
            .f-name {{ font-size: 0.8em; color: #7f8c8d; }}
            .f-price {{ font-weight: bold; margin: 2px 0; font-family: monospace; font-size: 1.1em; }}
            
            /* 安全板块特殊布局 */
            .split-section {{ display: flex; flex-direction: column; gap: 15px; }}
            .sub-header {{ font-size: 0.85em; font-weight: bold; color: #999; text-transform: uppercase; margin-bottom: 5px; display: block; }}

            @media (max-width: 768px) {{ .dashboard {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🚀 Geek Dashboard</h1>
                <span class="time">{date_str}</span>
            </header>
            
            <div class="dashboard">
                <div class="card readhub">
                    <h2>📰 ReadHub Tech</h2>
                    <ul>{readhub_html}</ul>
                </div>

                <div class="card security">
                    <h2>🛡️ Security Intel</h2>
                    <div class="split-section">
                        <div>
                            <span class="sub-header">Solidot / News</span>
                            <ul>{solidot_html}</ul>
                        </div>
                        <div>
                            <span class="sub-header" style="color:#e74c3c;">Latest CVE Alerts</span>
                            <ul>{cve_html}</ul>
                        </div>
                    </div>
                </div>

                <div class="card ai">
                    <h2>🤖 Hugging Face Trending</h2>
                    <ul>{hf_html}</ul>
                </div>
                
                <div class="card github">
                    <h2>🐍 GitHub Python</h2>
                    {github_html}
                </div>
                
                <div class="card finance">
                    <h2>💰 Market</h2>
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
    print(">>> 正在抓取 ReadHub...")
    readhub_data = get_readhub()
    
    print(">>> 正在抓取 Solidot & CVE...")
    solidot_data = get_solidot()
    cve_data = get_cve_alerts()
    
    print(">>> 正在抓取 Hugging Face...")
    hf_data = get_huggingface()
    
    print(">>> 正在抓取 GitHub...")
    github_data = get_github_trending()
    
    print(">>> 正在抓取 Finance...")
    finance_data = get_finance()
    
    print(">>> 生成页面...")
    generate_html(readhub_data, solidot_data, cve_data, hf_data, github_data, finance_data)
    print(">>> 完成! 请打开 index.html")