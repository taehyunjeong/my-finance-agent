import yfinance as yf
import os
import asyncio
import feedparser
import matplotlib.pyplot as plt
from telegram import Bot
from datetime import datetime
import io

# GitHub Secrets 설정
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

async def get_market_data_and_plot():
    tickers = {
        "S&P 500": "^GSPC", "Nasdaq": "^IXIC", 
        "USD/KRW": "KRW=X", "Gold": "GC=F", "BTC": "BTC-USD"
    }
    
    report = f"📅 {datetime.now().strftime('%Y-%m-%d')} 경제 리포트\n\n📊 [주요 지수 5일 추세]\n"
    
    # 그래프 설정
    plt.figure(figsize=(10, 6))
    
    for name, ticker in tickers.items():
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                diff_pct = ((curr - prev) / prev) * 100
                emoji = "🔺" if diff_pct > 0 else "🔻"
                report += f"• {name}: {curr:,.2f} ({emoji}{diff_pct:.2f}%)\n"
                
                # 그래프 그리기 (스케일이 다르므로 정규화해서 비교)
                normalized_series = (df['Close'] / df['Close'].iloc[0]) * 100
                plt.plot(df.index.strftime('%m/%d'), normalized_series, label=name, marker='o')
        except:
            report += f"• {name}: 데이터 오류\n"

    plt.title("5-Day Market Trend (Normalized)")
    plt.legend()
    plt.grid(True, linestyle='--')
    
    # 메모리에 그래프 이미지 저장
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return report, buf

async def get_top_news():
    # 뉴스 URL (구글 뉴스 경제 섹션)
    rss_url = "https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNR2h6Y0hKekp6RVNBZ0FmU2d3R29BQVAB?hl=ko&gl=KR&ceid=KR%3Ako"
    feed = feedparser.parse(rss_url)
    
    news_report = "\n📰 [오늘의 주요 뉴스 Top 5]\n"
    # 뉴스가 없을 경우를 대비해 확실히 루프를 돌립니다.
    count = 0
    for entry in feed.entries:
        if count >= 5: break
        title = entry.title.rsplit(" - ", 1)[0] # 언론사명 제거
        news_report += f"{count+1}. {title}\n"
        count += 1
    
    if count == 0:
        news_report += "현재 수집된 뉴스가 없습니다.\n"
        
    return news_report

async def main():
    market_text, chart_img = await get_market_data_and_plot()
    news_text = await get_top_news()
    
    final_text = market_text + news_text
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # 사진과 글을 함께 전송
    await bot.send_photo(chat_id=CHAT_ID, photo=chart_img, caption=final_text)

if __name__ == "__main__":
    asyncio.run(main())
