import requests
import datetime
import os

# 1. 抓取数据
def get_quote():
    try:
        url = "https://v1.hitokoto.cn/"
        res = requests.get(url).json()
        return f"{res['hitokoto']} —— {res['from']}"
    except Exception as e:
        return "今天网络有点累，暂无名言。"

# 2. 生成 HTML 内容
def generate_html(content):
    # 获取当前北京时间 (UTC+8)
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + datetime.timedelta(hours=8)
    date_str = beijing_time.strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>我的每日早报</title>
        <style>
            body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }}
            .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; }}
            .quote {{ font-size: 1.5em; color: #555; margin: 20px 0; font-style: italic; }}
            .time {{ color: #999; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>?? 每日早报</h1>
            <p class="quote">“{content}”</p>
            <p class="time">更新时间 (北京时间): {date_str}</p>
        </div>
    </body>
    </html>
    """
    
    # 3. 写入文件 index.html
    # 这样 GitHub Pages 默认就会展示这个文件
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    quote = get_quote()
    generate_html(quote)
    print("网页生成成功！")