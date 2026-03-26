import yfinance as yf
import os
import asyncio
import feedparser
from telegram import Bot
from datetime import datetime

# GitHub Secrets 설정
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

async def get_market_summary():
    # 추적할 지수 설정 (티커)
    tickers = {
        "S&P 500": "^GSPC",
        "나스닥": "^IXIC",
        "원/달러 환율": "KRW=X",
        "금 (선물)": "GC=F",
        "비트코인": "BTC-USD"
    }
    
    report = f"📅 {datetime.now().strftime('%Y-%m-%d')} 경제 리포트\n"
    report += "━━━━━━━━━━━━━━━━━━\n\n"
    report += "📊 *주요 시세 및 7일 추세*\n"
    
    for name, ticker in tickers.items():
        try:
            # 최근 7일간의 데이터를 가져옴
            df = yf.Ticker(ticker).history(period="7d")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                diff_pct = ((curr - prev) / prev) * 100
                emoji = "🔺" if diff_pct > 0 else "🔻"
                
                report += f"📍 *{name}*: {curr:,.2f} ({emoji}{diff_pct:.2f}%)\n"
                
                # 최근 5~7거래일 히스토리 (날짜와 종가)
                history_list = []
                for date, row in df.iterrows():
                    date_str = date.strftime('%m/%d')
                    history_list.append(f"{date_str}({row['Close']:,.0f})")
                
                report += "└ " + " ➔ ".join(history_list) + "\n\n"
        except Exception:
            report += f"❌ {name}: 데이터 수집 불가\n\n"
            
    return report

async def get_top_news():
    # 구글 뉴스 RSS (경제 섹션)
    rss_url = "https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNR2h6Y0hKekp6RVNBZ0FmU2d3R29BQVAB?hl=ko&gl=KR&ceid=KR%3Ako"
    feed = feedparser.parse(rss_url)
    
    news_report = "📰 *오늘의 경제 뉴스 Top 5*\n"
    # 상위 5개 뉴스 추출
    for i, entry in enumerate(feed.entries[:5]):
        # 뉴스 제목에서 언론사 이름 제거 시도 (선택 사항)
        title = entry.title.split(" - ")[0]
        news_report += f"{i+1}. {title}\n"
        # 상세 링크를 포함하고 싶다면 아래 주석 해제
        # news_report += f"🔗 [링크]({entry.link})\n"
    
    return news_report

async def main():
    market_data = await get_market_summary()
    news_data = await get_top_news()
    
    final_report = market_data + news_data + "\n━━━━━━━━━━━━━━━━━━"
    
    bot = Bot(token=TELEGRAM_TOKEN)
    # 마크다운 형식을 사용하여 깔끔하게 전송
    await bot.send_message(chat_id=CHAT_ID, text=final_report, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
