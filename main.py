#!/usr/bin/env python3
"""주식 자동 시장 분석 프로그램"""

import os
import sys
import argparse
from datetime import datetime

from config import AnalysisConfig
from analyzer.fetcher import fetch_stock_data, fetch_stock_info
from analyzer.demo_data import generate_demo_ohlcv, get_demo_info
from analyzer.technical import compute_all_indicators
from analyzer.signals import evaluate_signals, make_recommendation, AnalysisResult
from analyzer.reporter import plot_stock_chart, generate_text_report


def run_analysis(cfg: AnalysisConfig, tickers: list[str] | None = None,
                 demo: bool = False) -> list[AnalysisResult]:
    targets = tickers or cfg.tickers
    os.makedirs(cfg.report_dir, exist_ok=True)
    results = []

    for ticker in targets:
        mode_tag = "[데모]" if demo else ""
        print(f"\n[분석 중] {ticker} {mode_tag}...", end=" ", flush=True)

        if demo:
            df = generate_demo_ohlcv(ticker, cfg.lookback_days)
            info = get_demo_info(ticker)
        else:
            df = fetch_stock_data(ticker, cfg.lookback_days)
            if df is None or len(df) < cfg.ma_long:
                print(f"데이터 부족 → 데모 데이터로 대체")
                df = generate_demo_ohlcv(ticker, cfg.lookback_days)
                info = get_demo_info(ticker)
            else:
                info = fetch_stock_info(ticker)
        df = compute_all_indicators(df, cfg)
        signals = evaluate_signals(df, cfg)
        total_score = sum(s.score for s in signals)
        recommendation = make_recommendation(total_score, len(signals))

        result = AnalysisResult(
            ticker=ticker,
            info=info,
            signals=signals,
            total_score=total_score,
            recommendation=recommendation,
            df=df,
        )
        results.append(result)

        # 차트 저장
        chart_path = os.path.join(cfg.report_dir, f"{ticker.replace('.', '_')}_chart.png")
        plot_stock_chart(result, cfg, chart_path)
        print(f"완료 → [{recommendation}]  차트: {chart_path}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="주식 자동 시장 분석 프로그램")
    parser.add_argument("tickers", nargs="*", help="분석할 종목 티커 (예: AAPL MSFT 005930.KS)")
    parser.add_argument("--days", type=int, default=365, help="분석 기간(일), 기본값 365")
    parser.add_argument("--report-dir", default="reports", help="리포트 저장 디렉토리")
    parser.add_argument("--demo", action="store_true", help="시뮬레이션 데이터로 실행 (네트워크 불필요)")
    args = parser.parse_args()

    cfg = AnalysisConfig(
        lookback_days=args.days,
        report_dir=args.report_dir,
    )

    print("=" * 60)
    print("  주식 자동 시장 분석 프로그램")
    print(f"  분석 기간: 최근 {cfg.lookback_days}일")
    print("=" * 60)

    if args.demo:
        print("  [데모 모드] 시뮬레이션 데이터 사용")

    tickers = args.tickers if args.tickers else None
    results = run_analysis(cfg, tickers, demo=args.demo)

    if not results:
        print("\n분석 결과가 없습니다.")
        sys.exit(1)

    # 텍스트 리포트 출력 및 저장
    report = generate_text_report(results)
    print("\n" + report)

    report_path = os.path.join(cfg.report_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n리포트 저장: {report_path}")

    # 요약 (점수 순 정렬)
    print("\n[ 종합 순위 ]")
    sorted_results = sorted(results, key=lambda r: r.total_score, reverse=True)
    for i, r in enumerate(sorted_results, 1):
        name = r.info.get("name", r.ticker)
        print(f"  {i}. {r.ticker:12s} {name[:20]:20s}  {r.recommendation}")


if __name__ == "__main__":
    main()
