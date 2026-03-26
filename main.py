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
    
    # 개별 그래프를 그리기 위한 서브플롯 설정 (지수 개수만큼 세로로 배치)
    fig, axes = plt.subplots(len(tickers), 1, figsize=(8, 15))
    plt.subplots_adjust(hspace=0.5) # 그래프 간격 조정
    
    for i, (name, ticker) in enumerate(tickers.items()):
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if not df.empty:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                diff_pct = ((curr - prev) / prev) * 100
                emoji = "🔺" if diff_pct > 0 else "🔻"
                report += f"• {name}: {curr:,.2f} ({emoji}{diff_pct:.2f}%)\n"
                
                # 개별 그래프 그리기
                ax = axes[i]
                ax.plot(df.index.strftime('%m/%d'), df['Close'], marker='o', color='royalblue', linewidth=2)
                ax.set_title(f"{name} Trend (5 Days)", fontsize=12, fontweight='bold')
                ax.grid(True, linestyle='--', alpha=0.7)
                # Y축 라벨을 읽기 쉽게 천 단위 콤마 추가
                ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        except:
            report += f"• {name}: 데이터 로드 실패\n"

    # 메모리에 전체 그래프 이미지 저장
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return report, buf

async def get_top_news():
    rss_url = "https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNR2h6Y0hKekp6RVNBZ0FmU2d3R29BQVAB?hl=ko&gl=KR&ceid=KR%3Ako"
    feed = feedparser.parse(rss_url)
    
    news_report = "\n📰 [오늘의 주요 뉴스 Top 5]\n"
    for i, entry in enumerate(feed.entries[:5]):
        # 제목에서 언론사명 제거
        title = entry.title.rsplit(" - ", 1)[0]
        news_report += f"{i+1}. {title}\n"
    
    if not feed.entries:
        news_report += "현재 수집된 뉴스가 없습니다.\n"
        
    return news_report

async def get_top_news():
    # 더 안정적인 구글 뉴스 RSS 주소 (한국 경제 뉴스)
    rss_url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        # 뉴스 데이터를 가져옵니다.
        feed = feedparser.parse(rss_url)
        
        # 피드 자체가 비어있는지 확인
        if not feed.entries:
            # 예비 주소로 한 번 더 시도 (구글 뉴스 전체 경제 토픽)
            alt_url = "https://news.google.com/news/rss/headlines/section/topic/ECONOMY?hl=ko&gl=KR"
            feed = feedparser.parse(alt_url)

        news_report = "\n📰 [오늘의 주요 뉴스 Top 5]\n"
        count = 0
        
        for entry in feed.entries:
            if count >= 5: break
            # 제목 뒤에 붙는 언론사명 제거 (예: 제목 - 연합뉴스 -> 제목)
            title = entry.title.rsplit(" - ", 1)[0]
            news_report += f"{count+1}. {title}\n"
            count += 1
        
        if count == 0:
            return "\n📰 [오늘의 주요 뉴스]\n현재 구글 뉴스 서버에서 데이터를 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.\n"
            
        return news_report

    except Exception as e:
        return f"\n📰 [오늘의 주요 뉴스]\n뉴스 수집 중 오류가 발생했습니다: {str(e)}\n"

if __name__ == "__main__":
    asyncio.run(main())
