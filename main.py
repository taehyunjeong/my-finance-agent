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

async def get_market_data_and_plots():
    # WTI 유가(CL=F) 추가
    tickers = {
        "S&P 500": "^GSPC", "Nasdaq": "^IXIC", 
        "USD/KRW": "KRW=X", "WTI Oil": "CL=F", 
        "Gold": "GC=F", "BTC": "BTC-USD"
    }
    
    report = f"📅 {datetime.now().strftime('%Y-%m-%d')} 경제 리포트 (30일 추세)\n\n"
    
    # 지수가 6개로 늘어남에 따라 figsize 조정 (세로 길이 증가)
    fig, axes = plt.subplots(len(tickers), 1, figsize=(8, 22))
    plt.subplots_adjust(hspace=0.6)
    
    for i, (name, ticker) in enumerate(tickers.items()):
        try:
            # 기간을 30일(period="1mo")로 변경
            df = yf.Ticker(ticker).history(period="1mo")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                diff_pct = ((curr - prev) / prev) * 100
                emoji = "🔺" if diff_pct > 0 else "🔻"
                report += f"• {name}: {curr:,.2f} ({emoji}{diff_pct:.2f}%)\n"
                
                ax = axes[i]
                # 30일 데이터이므로 마커('o') 크기를 줄이거나 제거하여 선 위주로 표현
                ax.plot(df.index, df['Close'], color='royalblue', linewidth=2)
                ax.set_title(f"{name} Trend (30 Days)", fontsize=12, fontweight='bold')
                ax.grid(True, linestyle='--', alpha=0.5)
                
                # 날짜 간격 최적화 (데이터가 많으므로 일부만 표시)
                plt.setp(ax.get_xticklabels(), rotation=0, fontsize=9)
                ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        except Exception:
            report += f"• {name}: 데이터 로드 실패\n"

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return report, buf

async def get_top_news():
    rss_url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
    backup_url = "https://news.google.com/news/rss/headlines/section/topic/ECONOMY?hl=ko&gl=KR"
    
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            feed = feedparser.parse(backup_url)
            
        news_report = "\n📰 [오늘의 주요 뉴스 Top 5]\n"
        count = 0
        for entry in feed.entries:
            if count >= 5: break
            title = entry.title.rsplit(" - ", 1)[0]
            news_report += f"{count+1}. {title}\n"
            count += 1
            
        return news_report if count > 0 else "\n📰 [오늘의 주요 뉴스]\n현재 수집된 뉴스가 없습니다.\n"
    except Exception:
        return "\n📰 [오늘의 주요 뉴스]\n뉴스 데이터를 가져오는 중 오류가 발생했습니다.\n"

async def main():
    market_text, chart_img = await get_market_data_and_plots()
    news_text = await get_top_news()
    
    final_text = market_text + news_text
    bot = Bot(token=TELEGRAM_TOKEN)
    
    try:
        await bot.send_photo(chat_id=CHAT_ID, photo=chart_img, caption=final_text)
    except Exception:
        await bot.send_photo(chat_id=CHAT_ID, photo=chart_img)
        await bot.send_message(chat_id=CHAT_ID, text=final_text)

if __name__ == "__main__":
    asyncio.run(main())
