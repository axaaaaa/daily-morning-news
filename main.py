# -*- coding: utf-8 -*-
import requests
import datetime
import os

# 1. Fetch data
def get_quote():
    try:
        url = "https://v1.hitokoto.cn/"
        res = requests.get(url).json()
        return f"{res['hitokoto']} -- {res['from']}"
    except Exception as e:
        return "Network error, no quote today."

# 2. Generate HTML
def generate_html(content):
    # Get Beijing Time (UTC+8)
    utc_now = datetime.datetime.utcnow()
    beijing_time = utc_now + datetime.timedelta(hours=8)
    date_str = beijing_time.strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Daily News</title>
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
            <h1>📅 Daily Morning News</h1>
            <p class="quote">“{content}”</p>
            <p class="time">Update Time (Beijing): {date_str}</p>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    quote = get_quote()
    generate_html(quote)
    print("HTML generated successfully!")
