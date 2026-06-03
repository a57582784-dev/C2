import pandas as pd
import numpy as np
from config import AnalysisConfig


def add_moving_averages(df: pd.DataFrame, cfg: AnalysisConfig) -> pd.DataFrame:
    df[f"MA{cfg.ma_short}"] = df["Close"].rolling(cfg.ma_short).mean()
    df[f"MA{cfg.ma_mid}"] = df["Close"].rolling(cfg.ma_mid).mean()
    df[f"MA{cfg.ma_long}"] = df["Close"].rolling(cfg.ma_long).mean()
    df[f"EMA{cfg.ma_short}"] = df["Close"].ewm(span=cfg.ma_short, adjust=False).mean()
    return df


def add_rsi(df: pd.DataFrame, cfg: AnalysisConfig) -> pd.DataFrame:
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=cfg.rsi_period - 1, min_periods=cfg.rsi_period).mean()
    avg_loss = loss.ewm(com=cfg.rsi_period - 1, min_periods=cfg.rsi_period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def add_macd(df: pd.DataFrame, cfg: AnalysisConfig) -> pd.DataFrame:
    ema_fast = df["Close"].ewm(span=cfg.macd_fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=cfg.macd_slow, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD"].ewm(span=cfg.macd_signal, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    return df


def add_bollinger_bands(df: pd.DataFrame, cfg: AnalysisConfig) -> pd.DataFrame:
    mid = df["Close"].rolling(cfg.bb_period).mean()
    std = df["Close"].rolling(cfg.bb_period).std()
    df["BB_Upper"] = mid + cfg.bb_std * std
    df["BB_Mid"] = mid
    df["BB_Lower"] = mid - cfg.bb_std * std
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Mid"]
    df["BB_Pct"] = (df["Close"] - df["BB_Lower"]) / (df["BB_Upper"] - df["BB_Lower"])
    return df


def add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df["Volume_MA20"] = df["Volume"].rolling(20).mean()
    df["Volume_Ratio"] = df["Volume"] / df["Volume_MA20"]
    # OBV (On-Balance Volume)
    obv = [0]
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > df["Close"].iloc[i - 1]:
            obv.append(obv[-1] + df["Volume"].iloc[i])
        elif df["Close"].iloc[i] < df["Close"].iloc[i - 1]:
            obv.append(obv[-1] - df["Volume"].iloc[i])
        else:
            obv.append(obv[-1])
    df["OBV"] = obv
    return df


def compute_all_indicators(df: pd.DataFrame, cfg: AnalysisConfig) -> pd.DataFrame:
    df = add_moving_averages(df, cfg)
    df = add_rsi(df, cfg)
    df = add_macd(df, cfg)
    df = add_bollinger_bands(df, cfg)
    df = add_volume_indicators(df)
    return df
