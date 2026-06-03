import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def fetch_stock_data(ticker: str, days: int) -> Optional[pd.DataFrame]:
    """Yahoo Finance에서 주가 데이터를 가져옵니다."""
    end = datetime.today()
    start = end - timedelta(days=days)

    try:
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            return None
        # 멀티인덱스 컬럼 평탄화
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"[오류] {ticker} 데이터 수집 실패: {e}")
        return None


def fetch_stock_info(ticker: str) -> dict:
    """종목 기본 정보를 가져옵니다."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "name": info.get("longName") or info.get("shortName", ticker),
            "sector": info.get("sector", "N/A"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency", "USD"),
            "pe_ratio": info.get("trailingPE"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
        }
    except Exception:
        return {"name": ticker, "sector": "N/A", "currency": "USD"}
