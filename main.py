import yfinance as yf
import os
import asyncio
from telegram import Bot

# GitHub Secrets에서 정보를 가져옵니다.
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

async def get_economic_data():
    tickers = {
        "S&P 500": "^GSPC",
        "나스닥": "^IXIC",
        "원/달러 환율": "KRW=X",
        "금 (선물)": "GC=F",
        "비트코인": "BTC-USD"
    }
    report = "📈 [데일리 경제 리포트]\n\n"
    for name, ticker in tickers.items():
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) >= 2:
            curr = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2]
            diff = ((curr - prev) / prev) * 100
            emoji = "🔺" if diff > 0 else "🔻"
            report += f"{name}: {curr:,.2f} ({emoji}{diff:.2f}%)\n"
    return report

async def main():
    content = await get_economic_data()
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=content)

if __name__ == "__main__":
    asyncio.run(main())
