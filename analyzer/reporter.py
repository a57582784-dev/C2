import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime
from typing import List

from analyzer.signals import AnalysisResult
from config import AnalysisConfig

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


def _color(score: int) -> str:
    if score > 0:
        return "#2ecc71"
    elif score < 0:
        return "#e74c3c"
    return "#95a5a6"


def plot_stock_chart(result: AnalysisResult, cfg: AnalysisConfig, output_path: str) -> None:
    df = result.df
    ticker = result.ticker
    info = result.info

    fig = plt.figure(figsize=(16, 14))
    fig.patch.set_facecolor("#1a1a2e")
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.08)

    axes = [fig.add_subplot(gs[i]) for i in range(4)]
    for ax in axes:
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="#ecf0f1", labelsize=8)
        ax.spines["bottom"].set_color("#34495e")
        ax.spines["top"].set_color("#34495e")
        ax.spines["left"].set_color("#34495e")
        ax.spines["right"].set_color("#34495e")

    # ── 가격 차트 (ax0) ─────────────────────────────────────────
    ax0 = axes[0]
    close = df["Close"]
    ax0.plot(df.index, close, color="#3498db", linewidth=1.5, label="종가", zorder=3)

    if f"MA{cfg.ma_short}" in df.columns:
        ax0.plot(df.index, df[f"MA{cfg.ma_short}"], color="#f39c12", linewidth=1, label=f"MA{cfg.ma_short}", alpha=0.9)
    if f"MA{cfg.ma_mid}" in df.columns:
        ax0.plot(df.index, df[f"MA{cfg.ma_mid}"], color="#9b59b6", linewidth=1, label=f"MA{cfg.ma_mid}", alpha=0.9)
    if f"MA{cfg.ma_long}" in df.columns:
        ax0.plot(df.index, df[f"MA{cfg.ma_long}"], color="#e67e22", linewidth=1, label=f"MA{cfg.ma_long}", alpha=0.9)

    if "BB_Upper" in df.columns:
        ax0.fill_between(df.index, df["BB_Upper"], df["BB_Lower"],
                         alpha=0.08, color="#3498db", label="볼린저밴드")
        ax0.plot(df.index, df["BB_Upper"], color="#3498db", linewidth=0.5, linestyle="--", alpha=0.5)
        ax0.plot(df.index, df["BB_Lower"], color="#3498db", linewidth=0.5, linestyle="--", alpha=0.5)

    name = info.get("name", ticker)
    _REC_EN = {
        "강력 매수": "STRONG BUY", "매수 우세": "BUY",
        "강력 매도": "STRONG SELL", "매도 우세": "SELL", "중립 / 관망": "NEUTRAL",
    }
    rec_en = _REC_EN.get(result.recommendation, result.recommendation)
    rec_color = {"STRONG BUY": "#2ecc71", "BUY": "#27ae60",
                 "STRONG SELL": "#e74c3c", "SELL": "#c0392b"}.get(rec_en, "#95a5a6")
    ax0.set_title(
        f"{name} ({ticker})  |  Signal: {rec_en}  |  "
        f"Buy {result.buy_count} / Sell {result.sell_count}",
        color=rec_color, fontsize=13, fontweight="bold", pad=10
    )
    ax0.legend(loc="upper left", facecolor="#0f3460", edgecolor="#34495e",
               labelcolor="#ecf0f1", fontsize=8)
    ax0.set_ylabel("Price", color="#ecf0f1", fontsize=9)
    ax0.xaxis.set_visible(False)
    ax0.yaxis.set_label_coords(-0.05, 0.5)

    # ── Volume (ax1) ─────────────────────────────────────────────
    ax1 = axes[1]
    colors = ["#2ecc71" if c >= o else "#e74c3c"
              for c, o in zip(df["Close"], df["Open"])]
    ax1.bar(df.index, df["Volume"], color=colors, alpha=0.7, width=1)
    if "Volume_MA20" in df.columns:
        ax1.plot(df.index, df["Volume_MA20"], color="#f39c12", linewidth=1)
    ax1.set_ylabel("Volume", color="#ecf0f1", fontsize=9)
    ax1.xaxis.set_visible(False)

    # ── RSI (ax2) ────────────────────────────────────────────────
    ax2 = axes[2]
    if "RSI" in df.columns:
        ax2.plot(df.index, df["RSI"], color="#e74c3c", linewidth=1.2)
        ax2.axhline(cfg.rsi_overbought, color="#e74c3c", linewidth=0.7, linestyle="--", alpha=0.6,
                    label=f"OB({cfg.rsi_overbought:.0f})")
        ax2.axhline(cfg.rsi_oversold, color="#2ecc71", linewidth=0.7, linestyle="--", alpha=0.6,
                    label=f"OS({cfg.rsi_oversold:.0f})")
        ax2.axhline(50, color="#7f8c8d", linewidth=0.5, linestyle=":")
        ax2.fill_between(df.index, df["RSI"], cfg.rsi_oversold,
                         where=(df["RSI"] < cfg.rsi_oversold), alpha=0.3, color="#2ecc71")
        ax2.fill_between(df.index, df["RSI"], cfg.rsi_overbought,
                         where=(df["RSI"] > cfg.rsi_overbought), alpha=0.3, color="#e74c3c")
        ax2.set_ylim(0, 100)
    ax2.set_ylabel("RSI", color="#ecf0f1", fontsize=9)
    ax2.xaxis.set_visible(False)

    # ── MACD (ax3) ───────────────────────────────────────────────
    ax3 = axes[3]
    if "MACD" in df.columns:
        ax3.plot(df.index, df["MACD"], color="#3498db", linewidth=1.2, label="MACD")
        ax3.plot(df.index, df["MACD_Signal"], color="#e74c3c", linewidth=1.0, label="Signal")
        hist = df["MACD_Hist"]
        hist_colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in hist]
        ax3.bar(df.index, hist, color=hist_colors, alpha=0.6, width=1)
        ax3.axhline(0, color="#7f8c8d", linewidth=0.5)
        ax3.legend(loc="upper left", facecolor="#0f3460", edgecolor="#34495e",
                   labelcolor="#ecf0f1", fontsize=7)
    ax3.set_ylabel("MACD", color="#ecf0f1", fontsize=9)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=30, ha="right")

    plt.savefig(output_path, dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)


def generate_text_report(results: List[AnalysisResult]) -> str:
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append("=" * 70)
    lines.append(f"  주식 자동 시장 분석 리포트  |  {now}")
    lines.append("=" * 70)

    for res in results:
        name = res.info.get("name", res.ticker)
        close_series = res.df["Close"].dropna()
        if close_series.empty:
            continue
        close = close_series.iloc[-1]
        prev_close = close_series.iloc[-2] if len(close_series) > 1 else close
        change = (close - prev_close) / prev_close * 100
        sign = "▲" if change >= 0 else "▼"
        currency = res.info.get("currency", "USD")

        lines.append(f"\n{'─'*70}")
        lines.append(f"  {name}  ({res.ticker})")
        lines.append(f"  섹터: {res.info.get('sector', 'N/A')}  |  통화: {currency}")
        lines.append(f"  현재가: {close:,.2f}  {sign} {abs(change):.2f}%")
        pe = res.info.get("pe_ratio")
        if pe:
            lines.append(f"  PER: {pe:.1f}x")
        lines.append(f"  추천: [{res.recommendation}]  (매수신호 {res.buy_count}개 / 매도신호 {res.sell_count}개)")
        lines.append(f"  {'─'*40}")
        for sig in res.signals:
            icon = "▶" if sig.score > 0 else "◀" if sig.score < 0 else "●"
            lines.append(f"    {icon} [{sig.name}] {sig.detail}")

    lines.append(f"\n{'='*70}")
    lines.append("  ※ 본 분석은 참고용이며 투자 결정의 책임은 투자자에게 있습니다.")
    lines.append("=" * 70)
    return "\n".join(lines)
