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
    tickers = {
        "S&P 500": "^GSPC", "Nasdaq": "^IXIC", 
        "USD/KRW": "KRW=X", "Gold": "GC=F", "BTC": "BTC-USD"
    }
    
    report = f"📅 {datetime.now().strftime('%Y-%m-%d')} 경제 리포트\n\n"
    
    # 그래프 설정
    fig, axes = plt.subplots(len(tickers), 1, figsize=(8, 18))
    plt.subplots_adjust(hspace=0.6)
    
    for i, (name, ticker) in enumerate(tickers.items()):
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                diff_pct = ((curr - prev) / prev) * 100
                emoji = "🔺" if diff_pct > 0 else "🔻"
                report += f"• {name}: {curr:,.2f} ({emoji}{diff_pct:.2f}%)\n"
                
                ax = axes[i]
                ax.plot(df.index.strftime('%m/%d'), df['Close'], marker='o', color='royalblue', linewidth=2)
                ax.set_title(f"{name} Trend (5 Days)", fontsize=12, fontweight='bold')
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        except Exception as e:
            report += f"• {name}: 데이터 로드 실패\n"

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return report, buf

async def get_top_news():
    # 1순위: 구글 뉴스 비즈니스 섹션
    rss_url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
    # 2순위(예비): 구글 뉴스 경제 일반
    backup_url = "https://news.google.com/news/rss/headlines/section/topic/ECONOMY?hl=ko&gl=KR"
    
    try:
        feed = feedparser.parse(rss_url)
        
        # 만약 1순위 주소에서 뉴스가 안 오면 예비 주소 사용
        if not feed.entries:
            feed = feedparser.parse(backup_url)
            
        news_report = "\n📰 [오늘의 주요 뉴스 Top 5]\n"
        count = 0
        for entry in feed.entries:
            if count >= 5: break
            title = entry.title.rsplit(" - ", 1)[0]
            news_report += f"{count+1}. {title}\n"
            count += 1
            
        if count == 0:
            news_report += "현재 수집된 실시간 뉴스가 없습니다.\n"
            
        return news_report
    except Exception:
        return "\n📰 [오늘의 주요 뉴스]\n뉴스 데이터를 가져오는 중 오류가 발생했습니다.\n"

async def main():
    market_text, chart_img = await get_market_data_and_plots()
    news_text = await get_top_news()
    
    final_text = market_text + news_text
    bot = Bot(token=TELEGRAM_TOKEN)
    
    try:
        # 사진과 함께 텍스트 전송
        await bot.send_photo(chat_id=CHAT_ID, photo=chart_img, caption=final_text)
    except Exception:
        # 글자 수 초과 시 분할 전송
        await bot.send_photo(chat_id=CHAT_ID, photo=chart_img)
        await bot.send_message(chat_id=CHAT_ID, text=final_text)

if __name__ == "__main__":
    asyncio.run(main())
