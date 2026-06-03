import pandas as pd
from dataclasses import dataclass
from typing import List
from config import AnalysisConfig


@dataclass
class Signal:
    name: str
    score: int      # +1 매수, -1 매도, 0 중립
    detail: str


def _latest(df: pd.DataFrame, col: str):
    return df[col].dropna().iloc[-1] if col in df.columns else None


def evaluate_signals(df: pd.DataFrame, cfg: AnalysisConfig) -> List[Signal]:
    signals: List[Signal] = []
    close = _latest(df, "Close")

    # ── 이동평균 시그널 ──────────────────────────────────────────
    ma20 = _latest(df, f"MA{cfg.ma_short}")
    ma60 = _latest(df, f"MA{cfg.ma_mid}")
    ma120 = _latest(df, f"MA{cfg.ma_long}")

    if ma20 and ma60 and close:
        if close > ma20 > ma60:
            signals.append(Signal("MA 배열", +1, f"주가({close:.2f}) > MA{cfg.ma_short}({ma20:.2f}) > MA{cfg.ma_mid}({ma60:.2f}) — 정배열"))
        elif close < ma20 < ma60:
            signals.append(Signal("MA 배열", -1, f"주가({close:.2f}) < MA{cfg.ma_short}({ma20:.2f}) < MA{cfg.ma_mid}({ma60:.2f}) — 역배열"))
        else:
            signals.append(Signal("MA 배열", 0, "이동평균 혼조"))

    # 골든크로스 / 데드크로스 (최근 5일)
    if f"MA{cfg.ma_short}" in df.columns and f"MA{cfg.ma_mid}" in df.columns:
        recent = df[[f"MA{cfg.ma_short}", f"MA{cfg.ma_mid}"]].dropna().tail(6)
        if len(recent) >= 2:
            prev_diff = recent.iloc[-2][f"MA{cfg.ma_short}"] - recent.iloc[-2][f"MA{cfg.ma_mid}"]
            curr_diff = recent.iloc[-1][f"MA{cfg.ma_short}"] - recent.iloc[-1][f"MA{cfg.ma_mid}"]
            if prev_diff < 0 < curr_diff:
                signals.append(Signal("골든크로스", +1, f"MA{cfg.ma_short}이 MA{cfg.ma_mid}을 상향 돌파"))
            elif prev_diff > 0 > curr_diff:
                signals.append(Signal("데드크로스", -1, f"MA{cfg.ma_short}이 MA{cfg.ma_mid}을 하향 돌파"))

    # ── RSI 시그널 ──────────────────────────────────────────────
    rsi = _latest(df, "RSI")
    if rsi is not None:
        if rsi < cfg.rsi_oversold:
            signals.append(Signal("RSI", +1, f"RSI={rsi:.1f} — 과매도 (매수 기회)"))
        elif rsi > cfg.rsi_overbought:
            signals.append(Signal("RSI", -1, f"RSI={rsi:.1f} — 과매수 (매도 주의)"))
        else:
            signals.append(Signal("RSI", 0, f"RSI={rsi:.1f} — 중립 구간"))

    # ── MACD 시그널 ─────────────────────────────────────────────
    macd = _latest(df, "MACD")
    macd_sig = _latest(df, "MACD_Signal")
    macd_hist = _latest(df, "MACD_Hist")
    if macd is not None and macd_sig is not None:
        if macd > macd_sig and macd_hist and macd_hist > 0:
            signals.append(Signal("MACD", +1, f"MACD({macd:.3f}) > Signal({macd_sig:.3f}) — 상승 모멘텀"))
        elif macd < macd_sig:
            signals.append(Signal("MACD", -1, f"MACD({macd:.3f}) < Signal({macd_sig:.3f}) — 하락 모멘텀"))
        else:
            signals.append(Signal("MACD", 0, "MACD 중립"))

    # ── 볼린저밴드 시그널 ────────────────────────────────────────
    bb_pct = _latest(df, "BB_Pct")
    bb_upper = _latest(df, "BB_Upper")
    bb_lower = _latest(df, "BB_Lower")
    if bb_pct is not None and close and bb_upper and bb_lower:
        if bb_pct < 0.05:
            signals.append(Signal("볼린저밴드", +1, f"주가가 하단 밴드 근접 (BB%B={bb_pct:.2f}) — 반등 기대"))
        elif bb_pct > 0.95:
            signals.append(Signal("볼린저밴드", -1, f"주가가 상단 밴드 근접 (BB%B={bb_pct:.2f}) — 과열 주의"))
        else:
            signals.append(Signal("볼린저밴드", 0, f"BB%B={bb_pct:.2f} — 밴드 내 위치"))

    # ── 거래량 시그널 ────────────────────────────────────────────
    vol_ratio = _latest(df, "Volume_Ratio")
    if vol_ratio is not None:
        if vol_ratio > 2.0:
            signals.append(Signal("거래량", +1 if (close and ma20 and close > ma20) else -1,
                                  f"거래량 급증 (평균 대비 {vol_ratio:.1f}x)"))
        else:
            signals.append(Signal("거래량", 0, f"거래량 평범 ({vol_ratio:.2f}x)"))

    return signals


@dataclass
class AnalysisResult:
    ticker: str
    info: dict
    signals: List[Signal]
    total_score: int
    recommendation: str
    df: pd.DataFrame

    @property
    def buy_count(self) -> int:
        return sum(1 for s in self.signals if s.score > 0)

    @property
    def sell_count(self) -> int:
        return sum(1 for s in self.signals if s.score < 0)


def make_recommendation(score: int, total: int) -> str:
    if total == 0:
        return "분석 불가"
    ratio = score / total
    if ratio >= 0.5:
        return "강력 매수"
    elif ratio >= 0.2:
        return "매수 우세"
    elif ratio <= -0.5:
        return "강력 매도"
    elif ratio <= -0.2:
        return "매도 우세"
    else:
        return "중립 / 관망"
