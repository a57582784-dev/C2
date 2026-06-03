from dataclasses import dataclass, field
from typing import List


@dataclass
class AnalysisConfig:
    # 분석 대상 종목 (티커 심볼)
    tickers: List[str] = field(default_factory=lambda: [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "005930.KS",  # 삼성전자
        "000660.KS",  # SK하이닉스
    ])

    # 분석 기간 (일)
    lookback_days: int = 365

    # 단기/중기/장기 이동평균 기간
    ma_short: int = 20
    ma_mid: int = 60
    ma_long: int = 120

    # RSI 기간 및 임계값
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

    # MACD 파라미터
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # 볼린저밴드 파라미터
    bb_period: int = 20
    bb_std: float = 2.0

    # 리포트 출력 디렉토리
    report_dir: str = "reports"
