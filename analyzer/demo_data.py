"""실제 시장 데이터를 가져올 수 없을 때 사용하는 시뮬레이션 데이터 생성기."""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


_PROFILES = {
    "AAPL":    {"start": 170, "drift": 0.0008, "vol": 0.015, "name": "Apple Inc.", "sector": "Technology"},
    "MSFT":    {"start": 400, "drift": 0.0006, "vol": 0.013, "name": "Microsoft Corp.", "sector": "Technology"},
    "GOOGL":   {"start": 140, "drift": 0.0005, "vol": 0.016, "name": "Alphabet Inc.", "sector": "Technology"},
    "NVDA":    {"start": 800, "drift": 0.0012, "vol": 0.030, "name": "NVIDIA Corp.", "sector": "Technology"},
    "AMZN":    {"start": 180, "drift": 0.0007, "vol": 0.018, "name": "Amazon.com Inc.", "sector": "Consumer"},
    "005930.KS": {"start": 70000, "drift": 0.0003, "vol": 0.014, "name": "삼성전자", "sector": "Technology"},
    "000660.KS": {"start": 130000, "drift": 0.0004, "vol": 0.020, "name": "SK하이닉스", "sector": "Technology"},
}

_DEFAULT = {"start": 100, "drift": 0.0004, "vol": 0.015, "name": None, "sector": "N/A"}


def generate_demo_ohlcv(ticker: str, days: int, seed: int | None = None) -> pd.DataFrame:
    profile = _PROFILES.get(ticker, _DEFAULT)
    rng = np.random.default_rng(seed or hash(ticker) % (2**31))

    dates = pd.bdate_range(end=datetime.today(), periods=days)
    n = len(dates)

    returns = rng.normal(profile["drift"], profile["vol"], n)
    prices = profile["start"] * np.exp(np.cumsum(returns))

    high_adj = rng.uniform(0.005, 0.020, n)
    low_adj  = rng.uniform(0.005, 0.020, n)
    close = prices
    open_ = close * (1 + rng.normal(0, 0.005, n))
    high  = np.maximum(close, open_) * (1 + high_adj)
    low   = np.minimum(close, open_) * (1 - low_adj)
    vol_base = profile["start"] * 1_000_000
    volume = rng.integers(int(vol_base * 0.5), int(vol_base * 1.5), n).astype(float)

    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


def get_demo_info(ticker: str) -> dict:
    profile = _PROFILES.get(ticker, _DEFAULT)
    return {
        "name": profile["name"] or ticker,
        "sector": profile["sector"],
        "market_cap": None,
        "currency": "KRW" if ticker.endswith(".KS") else "USD",
        "pe_ratio": None,
        "52w_high": None,
        "52w_low": None,
    }
