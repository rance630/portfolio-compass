from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
PORTFOLIO_PATH = DATA_DIR / "portfolio.csv"
CASH_PATH = DATA_DIR / "cash.csv"
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="投資羅盤｜持股追蹤儀表板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Style ----------
st.markdown(
    """
    <style>
    :root {
        --bg: #081016;
        --panel: #101A22;
        --panel-2: #13212B;
        --line: #22323D;
        --ink: #EEF5F4;
        --muted: #96A7A4;
        --green: #45D39A;
        --green-soft: rgba(69, 211, 154, .13);
        --red: #F26D6D;
        --red-soft: rgba(242, 109, 109, .13);
        --gold: #E6C15C;
        --gold-soft: rgba(230, 193, 92, .14);
        --blue: #80BFFF;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(69, 211, 154, .13), transparent 28rem),
            linear-gradient(135deg, #081016 0%, #0B141B 48%, #101820 100%) !important;
        color: var(--ink) !important;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stToolbar"] { color: var(--muted) !important; }
    [data-testid="stSidebar"] {
        background: #0D171E !important;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] * { color: var(--ink) !important; }
    .main .block-container {
        max-width: 1480px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: inherit;
    }
    .hero {
        border: 1px solid var(--line);
        background: linear-gradient(135deg, rgba(16,26,34,.96), rgba(19,33,43,.88));
        border-radius: 26px;
        padding: 2rem 2.2rem;
        box-shadow: 0 18px 50px rgba(0,0,0,.25);
        margin-bottom: 1.25rem;
    }
    .eyebrow {
        display: inline-flex;
        gap: .45rem;
        align-items: center;
        color: var(--green) !important;
        background: var(--green-soft);
        border: 1px solid rgba(69,211,154,.22);
        border-radius: 999px;
        padding: .34rem .75rem;
        font-size: .86rem;
        font-weight: 700;
        margin-bottom: .9rem;
    }
    .hero h1 {
        font-size: clamp(2rem, 4vw, 3.1rem);
        line-height: 1.12;
        margin: 0 0 .8rem 0;
        letter-spacing: -0.04em;
        color: var(--ink) !important;
    }
    .hero p {
        color: var(--muted) !important;
        font-size: 1.04rem;
        max-width: 820px;
        line-height: 1.75;
        margin: 0;
    }
    .pill-row { display: flex; flex-wrap: wrap; gap: .55rem; margin: .95rem 0 1.2rem; }
    .pill {
        border: 1px solid var(--line);
        background: rgba(255,255,255,.035);
        color: #DDE8E6 !important;
        border-radius: 999px;
        padding: .45rem .75rem;
        font-size: .88rem;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(160px, 1fr));
        gap: .95rem;
        margin: .9rem 0 1.1rem;
    }
    .metric-card {
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(19,33,43,.95), rgba(16,26,34,.95));
        border-radius: 20px;
        padding: 1.05rem 1.05rem 1rem;
        min-height: 122px;
        box-shadow: 0 12px 26px rgba(0,0,0,.22);
    }
    .metric-label { color: var(--muted) !important; font-size: .88rem; font-weight: 700; margin-bottom: .55rem; }
    .metric-value { color: var(--ink) !important; font-size: 1.72rem; font-weight: 800; letter-spacing: -0.03em; }
    .metric-sub { color: var(--muted) !important; font-size: .82rem; margin-top: .35rem; }
    .gain { color: var(--green) !important; }
    .loss { color: var(--red) !important; }
    .flat { color: var(--gold) !important; }
    .panel {
        border: 1px solid var(--line);
        background: rgba(16,26,34,.92);
        border-radius: 22px;
        padding: 1.25rem 1.35rem;
        box-shadow: 0 12px 34px rgba(0,0,0,.22);
        margin-bottom: 1rem;
    }
    .panel h3 { margin-top: 0; color: var(--ink) !important; }
    .note {
        border-left: 4px solid var(--green);
        background: rgba(69,211,154,.08);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        color: #DDE8E6 !important;
        line-height: 1.8;
    }
    .warn {
        border-left: 4px solid var(--gold);
        background: var(--gold-soft);
        border-radius: 16px;
        padding: .85rem 1rem;
        color: #F7E9BD !important;
        line-height: 1.7;
    }
    .empty {
        border: 1px dashed #355263;
        background: rgba(128,191,255,.05);
        border-radius: 20px;
        padding: 2rem;
        color: var(--muted) !important;
        text-align: center;
    }
    .small-muted { color: var(--muted) !important; font-size: .9rem; line-height: 1.7; }
    div[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 16px; overflow: hidden; }
    .stButton > button {
        width: 100%;
        border-radius: 14px !important;
        border: 1px solid rgba(69,211,154,.35) !important;
        background: linear-gradient(135deg, #2E8A68, #266E58) !important;
        color: white !important;
        font-weight: 800 !important;
        padding: .78rem 1rem !important;
        box-shadow: 0 10px 22px rgba(38,110,88,.22) !important;
    }
    .stDownloadButton > button {
        border-radius: 14px !important;
        border: 1px solid var(--line) !important;
        background: rgba(255,255,255,.04) !important;
        color: var(--ink) !important;
        font-weight: 700 !important;
    }
    div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
        background: #111D26 !important;
        border-color: var(--line) !important;
        color: var(--ink) !important;
    }
    input, textarea { color: var(--ink) !important; }
    [data-testid="stTabs"] button p { color: var(--muted) !important; font-weight: 800; }
    [data-testid="stTabs"] button[aria-selected="true"] p { color: var(--green) !important; }
    [data-testid="stFileUploader"] { color: var(--ink) !important; }
    .element-container:has(.hide-streamlit-broken-icons) + div { display: none !important; }
    @media (max-width: 980px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 620px) { .metric-grid { grid-template-columns: 1fr; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Utility ----------
DEFAULT_COLUMNS = ["股票代號", "股數", "平均成本", "買入日期", "備註"]


def ensure_portfolio_file() -> None:
    if not PORTFOLIO_PATH.exists():
        pd.DataFrame(columns=DEFAULT_COLUMNS).to_csv(PORTFOLIO_PATH, index=False, encoding="utf-8-sig")


def normalize_ticker(ticker: object) -> str:
    """把使用者輸入的股票代號整理成 Yahoo Finance 可讀格式。

    Streamlit 的資料表在新增空白列時，空白欄位有時會被 pandas 當成 float/NaN，
    不能直接呼叫 .strip()，所以這裡先統一轉成安全字串。
    """
    if ticker is None:
        return ""
    try:
        if pd.isna(ticker):
            return ""
    except TypeError:
        pass
    return str(ticker).strip().upper()


def load_portfolio() -> pd.DataFrame:
    ensure_portfolio_file()
    df = pd.read_csv(PORTFOLIO_PATH)
    for col in DEFAULT_COLUMNS:
        if col not in df.columns:
            df[col] = "" if col in ["股票代號", "買入日期", "備註"] else 0.0
    df = df[DEFAULT_COLUMNS].copy()
    df["股票代號"] = df["股票代號"].map(normalize_ticker)
    df["股數"] = pd.to_numeric(df["股數"], errors="coerce").fillna(0.0)
    df["平均成本"] = pd.to_numeric(df["平均成本"], errors="coerce").fillna(0.0)
    df["買入日期"] = pd.to_datetime(df["買入日期"], errors="coerce").dt.date.astype("string").fillna("")
    df["備註"] = df["備註"].fillna("").astype(str)
    df = df[(df["股票代號"] != "") & (df["股數"] > 0)]
    return df.reset_index(drop=True)


def save_portfolio(df: pd.DataFrame) -> None:
    clean = df.copy()
    for col in DEFAULT_COLUMNS:
        if col not in clean.columns:
            clean[col] = "" if col in ["股票代號", "買入日期", "備註"] else 0.0
    clean = clean[DEFAULT_COLUMNS]
    clean["股票代號"] = clean["股票代號"].map(normalize_ticker)
    clean["股數"] = pd.to_numeric(clean["股數"], errors="coerce").fillna(0.0)
    clean["平均成本"] = pd.to_numeric(clean["平均成本"], errors="coerce").fillna(0.0)
    clean = clean[(clean["股票代號"] != "") & (clean["股數"] > 0)]
    clean.to_csv(PORTFOLIO_PATH, index=False, encoding="utf-8-sig")


def ensure_cash_file() -> None:
    if not CASH_PATH.exists():
        pd.DataFrame([{"現金水位（台幣）": 0.0}]).to_csv(CASH_PATH, index=False, encoding="utf-8-sig")


def load_cash_twd() -> float:
    ensure_cash_file()
    try:
        df = pd.read_csv(CASH_PATH)
        if "現金水位（台幣）" in df.columns and not df.empty:
            value = pd.to_numeric(df["現金水位（台幣）"], errors="coerce").fillna(0).iloc[0]
            return max(float(value), 0.0)
    except Exception:
        pass
    return 0.0


def save_cash_twd(value: float) -> None:
    pd.DataFrame([{"現金水位（台幣）": max(float(value), 0.0)}]).to_csv(CASH_PATH, index=False, encoding="utf-8-sig")


def money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"${value:,.2f}"


def money_twd(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"NT${value:,.0f}"


def money_by_currency(value: float | int | None, currency: str) -> str:
    if value is None or pd.isna(value):
        return "—"
    currency = str(currency).upper()
    if currency == "TWD":
        return f"NT${value:,.0f}"
    return f"US${value:,.2f}"


def ticker_currency(ticker: str) -> str:
    ticker = normalize_ticker(ticker)
    if ticker.endswith(".TW") or ticker.endswith(".TWO"):
        return "TWD"
    return "USD"


def currency_rate_to_twd(currency: str, usd_twd_rate: float) -> float:
    return 1.0 if currency == "TWD" else float(usd_twd_rate)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_usd_twd_rate() -> float:
    try:
        raw = yf.download("TWD=X", period="5d", auto_adjust=True, progress=False)
        if raw is not None and not raw.empty:
            close = raw["Close"].dropna()
            if not close.empty:
                value = close.iloc[-1]
                if hasattr(value, "iloc"):
                    value = value.iloc[0]
                return float(value)
    except Exception:
        pass
    return 31.5


def pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value * 100:,.2f}%"


def number(value: float | int | None, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.{digits}f}"


def css_class_for_value(value: float) -> str:
    if value > 0:
        return "gain"
    if value < 0:
        return "loss"
    return "flat"


@st.cache_data(ttl=900, show_spinner=False)
def fetch_prices(tickers: tuple[str, ...], start: str, end: str) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()
    raw = yf.download(
        list(tickers),
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )
    if raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            prices = raw["Close"].copy()
        elif "Adj Close" in raw.columns.get_level_values(0):
            prices = raw["Adj Close"].copy()
        else:
            prices = raw.xs(raw.columns.get_level_values(0)[0], axis=1, level=0)
    else:
        prices = raw[["Close"]].copy() if "Close" in raw.columns else raw.copy()
        if len(tickers) == 1:
            prices.columns = [tickers[0]]
    prices = prices.dropna(how="all")
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(tickers[0])
    prices = prices.ffill().dropna(how="all")
    prices.columns = [str(c).upper() for c in prices.columns]
    return prices


def build_holdings_snapshot(portfolio: pd.DataFrame, prices: pd.DataFrame, usd_twd_rate: float) -> pd.DataFrame:
    if portfolio.empty or prices.empty:
        return pd.DataFrame()
    latest_prices = prices.ffill().iloc[-1]
    rows = []
    for _, row in portfolio.iterrows():
        ticker = normalize_ticker(row["股票代號"])
        if ticker not in latest_prices.index or pd.isna(latest_prices[ticker]):
            continue
        shares = float(row["股數"])
        avg_cost = float(row["平均成本"])
        current_price = float(latest_prices[ticker])
        currency = ticker_currency(ticker)
        fx = currency_rate_to_twd(currency, usd_twd_rate)
        cost = shares * avg_cost
        market_value = shares * current_price
        cost_twd = cost * fx
        market_value_twd = market_value * fx
        pnl_twd = market_value_twd - cost_twd
        pnl_pct = np.nan if cost_twd <= 0 else pnl_twd / cost_twd
        buy_date = row.get("買入日期", "")
        rows.append(
            {
                "股票代號": ticker,
                "幣別": currency,
                "股數": shares,
                "平均成本": avg_cost,
                "現價": current_price,
                "投入成本": cost,
                "目前市值": market_value,
                "投入成本（台幣）": cost_twd,
                "目前市值（台幣）": market_value_twd,
                "未實現損益（台幣）": pnl_twd,
                "報酬率": pnl_pct,
                "買入日期": buy_date,
                "備註": row.get("備註", ""),
            }
        )
    snapshot = pd.DataFrame(rows)
    if not snapshot.empty:
        total_value = snapshot["目前市值（台幣）"].sum()
        snapshot["持股占比"] = snapshot["目前市值（台幣）"] / total_value if total_value > 0 else np.nan
    return snapshot


def portfolio_value_series(snapshot: pd.DataFrame, prices: pd.DataFrame, usd_twd_rate: float) -> pd.Series:
    if snapshot.empty or prices.empty:
        return pd.Series(dtype=float)

    # 同一檔股票可能被新增多次，例如分批買進 QCOM。
    # 先依股票代號彙總股數，避免 prices[tickers] 出現重複欄位，造成 pandas reindex 錯誤。
    value_weights: dict[str, float] = {}
    for _, row in snapshot.iterrows():
        ticker = str(row.get("股票代號", "")).strip().upper()
        if not ticker or ticker not in prices.columns:
            continue
        shares = float(row.get("股數", 0) or 0)
        rate = currency_rate_to_twd(str(row.get("幣別", "USD")), usd_twd_rate)
        value_weights[ticker] = value_weights.get(ticker, 0.0) + shares * rate

    if not value_weights:
        return pd.Series(dtype=float)

    tickers = list(value_weights.keys())
    weights = pd.Series(value_weights, dtype=float)
    series = prices.loc[:, tickers].ffill().dropna(how="all").mul(weights, axis=1).sum(axis=1)
    return series.rename("投資組合市值（台幣）")


def make_fig_dark(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font=dict(color="#DCE8E6", family="Arial"),
        height=height,
        margin=dict(l=18, r=18, t=52, b=28),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.08)")
    return fig


def metric_card(label: str, value: str, sub: str = "", cls: str = "") -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {cls}">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """


def concentration_label(max_weight: float) -> str:
    if pd.isna(max_weight):
        return "資料不足"
    if max_weight >= 0.45:
        return "高度集中"
    if max_weight >= 0.30:
        return "略為集中"
    return "分散尚可"


def return_label(total_return: float) -> str:
    if pd.isna(total_return):
        return "資料不足"
    if total_return >= 0.20:
        return "表現強勁"
    if total_return >= 0.05:
        return "正向成長"
    if total_return >= -0.05:
        return "接近持平"
    return "需要檢視"


def beginner_explanation(snapshot: pd.DataFrame, total_cost: float, total_value: float, total_pnl: float, total_return: float, cash_twd: float = 0.0) -> str:
    if snapshot.empty:
        return "目前還沒有持股資料。新增持股後，系統會幫你整理總市值、總成本、未實現損益與持股占比。"
    largest = snapshot.sort_values("持股占比", ascending=False).iloc[0]
    direction = "獲利" if total_pnl > 0 else "虧損" if total_pnl < 0 else "持平"
    concentration = concentration_label(float(largest["持股占比"]))
    total_assets = total_value + cash_twd
    cash_ratio = np.nan if total_assets <= 0 else cash_twd / total_assets
    risk_sentence = (
        f"最大持股是 {largest['股票代號']}，占股票部位約 {pct(largest['持股占比'])}，目前集中度判斷為「{concentration}」。"
    )
    if largest["持股占比"] >= 0.35:
        risk_sentence += " 這代表單一股票漲跌會明顯影響整體投資組合，建議留意是否過度集中。"
    else:
        risk_sentence += " 目前沒有明顯單一持股過重的問題，但仍應定期檢查產業與個股分散程度。"
    cash_sentence = "" if cash_twd <= 0 else f" 目前現金水位約 {money_twd(cash_twd)}，占總資產約 {pct(cash_ratio)}。"
    return (
        f"你的股票部位總投入約 {money_twd(total_cost)}，目前股票市值約 {money_twd(total_value)}，"
        f"整體呈現{direction}，未實現損益為 {money_twd(total_pnl)}，股票報酬率約 {pct(total_return)}。"
        f"{cash_sentence}{risk_sentence} 對新手來說，除了看賺賠，也要看資金是否集中在少數股票，以及現金是否足以應付短期波動或加碼機會。"
    )


def portfolio_review(snapshot: pd.DataFrame, stock_value_twd: float, cash_twd: float, total_return: float, annual_vol: float, max_drawdown: float, sharpe: float) -> list[str]:
    total_assets = stock_value_twd + cash_twd
    cash_ratio = np.nan if total_assets <= 0 else cash_twd / total_assets
    stock_ratio = np.nan if total_assets <= 0 else stock_value_twd / total_assets
    largest = snapshot.sort_values("持股占比", ascending=False).iloc[0] if not snapshot.empty else None
    suggestions: list[str] = []

    if not pd.isna(total_return):
        if total_return > 0.15:
            suggestions.append("股票部位目前報酬表現較強，但仍要確認獲利是否集中在少數持股。")
        elif total_return < -0.10:
            suggestions.append("股票部位目前虧損較明顯，建議檢視虧損是否來自單一股票、產業集中，或原本投資假設已改變。")
        else:
            suggestions.append("股票部位目前報酬接近中性，可把重點放在配置是否符合自己的風險承受度。")

    if largest is not None:
        if largest["持股占比"] >= 0.45:
            suggestions.append(f"{largest['股票代號']} 占股票部位 {pct(largest['持股占比'])}，集中度偏高；若它大幅波動，整體資產會受到明顯影響。")
        elif largest["持股占比"] >= 0.30:
            suggestions.append(f"最大持股 {largest['股票代號']} 占比約 {pct(largest['持股占比'])}，仍在可觀察範圍，但不宜繼續無意識加重。")
        else:
            suggestions.append("單一持股集中度目前相對可控，之後可再觀察產業是否過度集中。")

    if not pd.isna(cash_ratio):
        if cash_ratio < 0.05:
            suggestions.append("現金比例低於 5%，代表幾乎滿倉；若遇到市場下跌，彈性會比較小。")
        elif cash_ratio > 0.35:
            suggestions.append("現金比例偏高，防守性較強；若你的目標是長期成長，可以思考是否有分批投入計畫。")
        else:
            suggestions.append(f"目前股票約 {pct(stock_ratio)}、現金約 {pct(cash_ratio)}，整體攻守配置相對清楚。")

    if not pd.isna(max_drawdown):
        if max_drawdown <= -0.30:
            suggestions.append("歷史最大回撤超過 30%，表示這個組合可能出現較深下跌，新手要先確認自己能否承受。")
        elif max_drawdown <= -0.15:
            suggestions.append("歷史回撤屬於中等偏高，建議搭配現金水位或較分散的 ETF 來降低心理壓力。")

    if not pd.isna(sharpe):
        if sharpe >= 1:
            suggestions.append("夏普比率高於 1，代表目前風險調整後表現不錯，但仍需搭配回撤與集中度一起看。")
        elif sharpe < 0:
            suggestions.append("夏普比率為負，代表承擔波動後沒有換到理想報酬，建議重新檢視配置。")

    return suggestions[:5]


def price_start_date(portfolio: pd.DataFrame) -> date:
    parsed = pd.to_datetime(portfolio.get("買入日期", pd.Series(dtype=str)), errors="coerce")
    if parsed.notna().any():
        return max(parsed.min().date() - timedelta(days=7), date(1990, 1, 1))
    return date.today() - timedelta(days=365 * 3)

# ---------- Data ----------
portfolio = load_portfolio()
cash_twd = load_cash_twd()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 持股設定")
    st.caption("新增你真的持有的股票，系統會自動抓現價並計算損益。")

    with st.form("add_holding", clear_on_submit=True):
        st.markdown("### 新增持股")
        ticker = st.text_input("股票代號", placeholder="例如 AAPL、MSFT、2330.TW")
        shares = st.number_input("持有股數", min_value=0.0, value=0.0, step=1.0)
        avg_cost = st.number_input("平均成本", min_value=0.0, value=0.0, step=1.0)
        buy_date = st.date_input("買入日期", value=date.today() - timedelta(days=365))
        note = st.text_input("備註（可空白）", placeholder="例如 長期持有、ETF、觀察中")
        submitted = st.form_submit_button("加入持股")

    if submitted:
        if not normalize_ticker(ticker):
            st.error("請輸入股票代號。")
        elif shares <= 0:
            st.error("股數必須大於 0。")
        elif avg_cost <= 0:
            st.error("平均成本必須大於 0。")
        else:
            new_row = pd.DataFrame(
                [{"股票代號": normalize_ticker(ticker), "股數": shares, "平均成本": avg_cost, "買入日期": buy_date.isoformat(), "備註": note}]
            )
            save_portfolio(pd.concat([portfolio, new_row], ignore_index=True))
            st.success("已加入持股。")
            st.rerun()

    st.markdown("---")
    st.markdown("### 現金水位")
    cash_input = st.number_input("目前現金（台幣）", min_value=0.0, value=float(cash_twd), step=1000.0, help="用來計算整體資產中現金與股票的比例。")
    if st.button("儲存現金水位"):
        save_cash_twd(cash_input)
        st.success("已更新現金水位。")
        st.rerun()

    st.markdown("---")
    st.markdown("### 資料設定")
    benchmark = normalize_ticker(st.text_input("比較基準", value="SPY", help="常見：SPY、QQQ、0050.TW"))
    show_advanced = st.toggle("顯示進階設定", value=False)
    if show_advanced:
        annualization_factor = st.selectbox("年化頻率", [252, 365, 52, 12], index=0, format_func=lambda x: f"{x} 期")
        risk_free_rate = st.number_input("無風險利率（年化 %）", min_value=0.0, max_value=20.0, value=2.0, step=0.25) / 100
        lookback_years = st.slider("績效圖最長回看年數", min_value=1, max_value=10, value=5)
    else:
        annualization_factor = 252
        risk_free_rate = 0.02
        lookback_years = 5

    st.markdown("---")
    st.download_button(
        "下載持股 CSV",
        data=portfolio.to_csv(index=False).encode("utf-8-sig"),
        file_name="portfolio.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ---------- Hero ----------
st.markdown(
    """
    <section class="hero">
        <div class="eyebrow">Portfolio Compass｜投資羅盤</div>
        <h1>我的持股追蹤儀表板</h1>
        <p>記錄自己的持股、成本與買入日期，自動抓取現價，整理總損益、資產配置與風險提醒。介面以新手也能理解的方式呈現，不只看報酬，也看風險與集中度。</p>
    </section>
    """,
    unsafe_allow_html=True,
)

if portfolio.empty:
    st.markdown(
        """
        <div class="empty">
            <h3>尚未建立持股紀錄</h3>
            <p>請先到左側新增一筆持股，例如股票代號 AAPL、股數 5、平均成本 180。新增後，這裡會自動顯示你的總市值、損益、資產配置與新手風險提醒。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

all_tickers = sorted(set(portfolio["股票代號"].tolist() + ([benchmark] if benchmark else [])))
start_dt = max(price_start_date(portfolio), date.today() - timedelta(days=365 * lookback_years))
end_dt = date.today() + timedelta(days=1)

with st.spinner("正在取得最新股價資料..."):
    prices = fetch_prices(tuple(all_tickers), start_dt.isoformat(), end_dt.isoformat())

if prices.empty:
    st.error("無法取得股價資料。請確認股票代號是否正確，例如美股 AAPL、台股 2330.TW。")
    st.stop()

usd_twd_rate = fetch_usd_twd_rate()
snapshot = build_holdings_snapshot(portfolio, prices, usd_twd_rate)
if snapshot.empty:
    st.error("目前持股都無法對應到股價資料。請檢查股票代號是否正確。")
    st.stop()

missing = sorted(set(portfolio["股票代號"]) - set(snapshot["股票代號"]))
if missing:
    st.warning(f"以下股票暫時無法取得價格，已先排除：{', '.join(missing)}")

# ---------- Portfolio calculations ----------
total_cost = float(snapshot["投入成本（台幣）"].sum())
stock_value_twd = float(snapshot["目前市值（台幣）"].sum())
total_value = stock_value_twd
total_assets_twd = stock_value_twd + cash_twd
stock_ratio_total = np.nan if total_assets_twd <= 0 else stock_value_twd / total_assets_twd
cash_ratio_total = np.nan if total_assets_twd <= 0 else cash_twd / total_assets_twd
total_pnl = stock_value_twd - total_cost
total_return = np.nan if total_cost <= 0 else total_pnl / total_cost
largest_weight = float(snapshot["持股占比"].max()) if not snapshot.empty else np.nan
series = portfolio_value_series(snapshot, prices, usd_twd_rate)
returns = series.pct_change().dropna() if not series.empty else pd.Series(dtype=float)
annual_vol = float(returns.std(ddof=1) * np.sqrt(annualization_factor)) if len(returns) > 2 else np.nan
annual_return = float((series.iloc[-1] / series.iloc[0]) ** (annualization_factor / max(len(returns), 1)) - 1) if len(series) > 2 and series.iloc[0] > 0 else np.nan
sharpe = np.nan if pd.isna(annual_vol) or annual_vol == 0 else (annual_return - risk_free_rate) / annual_vol
running_peak = series.cummax() if not series.empty else pd.Series(dtype=float)
drawdown = (series / running_peak - 1).dropna() if not series.empty else pd.Series(dtype=float)
max_drawdown = float(drawdown.min()) if not drawdown.empty else np.nan

st.markdown(
    f"""
    <div class="pill-row">
        <div class="pill">資料來源：Yahoo Finance</div>
        <div class="pill">持股數：{len(snapshot)}</div>
        <div class="pill">最新日期：{prices.index.max().date()}</div>
        <div class="pill">美元兌台幣：約 {usd_twd_rate:.2f}</div>
        <div class="pill">股票：{pct(stock_ratio_total)}</div>
        <div class="pill">現金：{pct(cash_ratio_total)}</div>
        <div class="pill">比較基準：{benchmark or '未設定'}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

pnl_cls = css_class_for_value(total_pnl)
return_cls = css_class_for_value(total_return if not pd.isna(total_return) else 0)
concentration = concentration_label(largest_weight)

st.markdown("### 今日總覽")
metric_items = [
    ("總資產", money_twd(total_assets_twd), "股票市值 + 現金水位"),
    ("股票市值", money_twd(stock_value_twd), "已換算為台幣"),
    ("現金水位", money_twd(cash_twd), f"現金占比 {pct(cash_ratio_total)}", "flat"),
    ("股票比例", pct(stock_ratio_total), "股票占總資產比例"),
    ("未實現損益", money_twd(total_pnl), return_label(total_return), pnl_cls),
    ("最大持股占比", pct(largest_weight), concentration, "gain" if largest_weight < 0.30 else "flat" if largest_weight < 0.45 else "loss"),
]
cols = st.columns(6)
for col, item in zip(cols, metric_items):
    label, value, sub = item[0], item[1], item[2]
    cls = item[3] if len(item) > 3 else ""
    col.markdown(metric_card(label, value, sub, cls), unsafe_allow_html=True)

col_a, col_b = st.columns([1.25, 0.9], gap="large")
with col_a:
    st.markdown("<div class='panel'><h3>新手看得懂的投資摘要</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='note'>{beginner_explanation(snapshot, total_cost, stock_value_twd, total_pnl, total_return, cash_twd)}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
with col_b:
    st.markdown("<div class='panel'><h3>風險檢查</h3>", unsafe_allow_html=True)
    risk_rows = [
        ("股票 / 現金", f"{pct(stock_ratio_total)} / {pct(cash_ratio_total)}"),
        ("最大持股", snapshot.sort_values("持股占比", ascending=False).iloc[0]["股票代號"]),
        ("集中度", concentration),
        ("年化波動", pct(annual_vol)),
        ("最大回撤", pct(max_drawdown)),
        ("夏普比率", number(sharpe)),
    ]
    for label, val in risk_rows:
        st.markdown(
            f"<div style='display:flex; justify-content:space-between; border-bottom:1px solid var(--line); padding:.62rem 0;'><span style='color:var(--muted)'>{label}</span><strong>{val}</strong></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='panel'><h3>投資組合檢視建議</h3>", unsafe_allow_html=True)
for suggestion in portfolio_review(snapshot, stock_value_twd, cash_twd, total_return, annual_vol, max_drawdown, sharpe):
    st.markdown(f"<div style='border-bottom:1px solid var(--line); padding:.62rem 0; color:#DDE8E6;'>• {suggestion}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---------- Tabs ----------
tab_overview, tab_holdings, tab_allocation, tab_performance, tab_learn = st.tabs(
    ["總覽", "持股管理", "資產配置", "績效追蹤", "新手說明"]
)

with tab_overview:
    st.markdown("### 持股損益表")
    display = snapshot.copy()
    display["股數"] = display["股數"].map(lambda x: number(x, 4).rstrip("0").rstrip("."))

    # 原始「平均成本 / 現價 / 投入成本 / 目前市值」會依個股幣別顯示；
    # 台幣換算欄位則統一顯示 NT$。避免把不存在的「未實現損益」欄位拿來格式化。
    if "平均成本" in display.columns:
        display["平均成本"] = [money_by_currency(v, cur) for v, cur in zip(snapshot["平均成本"], snapshot["幣別"])]
    if "現價" in display.columns:
        display["現價"] = [money_by_currency(v, cur) for v, cur in zip(snapshot["現價"], snapshot["幣別"])]
    if "投入成本" in display.columns:
        display["投入成本"] = [money_by_currency(v, cur) for v, cur in zip(snapshot["投入成本"], snapshot["幣別"])]
    if "目前市值" in display.columns:
        display["目前市值"] = [money_by_currency(v, cur) for v, cur in zip(snapshot["目前市值"], snapshot["幣別"])]

    for c in ["投入成本（台幣）", "目前市值（台幣）", "未實現損益（台幣）"]:
        if c in display.columns:
            display[c] = display[c].map(money_twd)
    for c in ["報酬率", "持股占比"]:
        if c in display.columns:
            display[c] = display[c].map(pct)

    st.dataframe(
        display[["股票代號", "幣別", "股數", "平均成本", "現價", "投入成本（台幣）", "目前市值（台幣）", "未實現損益（台幣）", "報酬率", "持股占比", "買入日期", "備註"]],
        use_container_width=True,
        hide_index=True,
    )

    if not series.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series.index, y=series, mode="lines", name="投資組合市值", line=dict(color="#45D39A", width=2.8)))
        fig.update_layout(title="投資組合市值走勢", yaxis_title="市值")
        fig = make_fig_dark(fig, 440)
        st.plotly_chart(fig, use_container_width=True)

with tab_holdings:
    st.markdown("### 編輯持股紀錄")
    st.markdown("<p class='small-muted'>你可以直接在表格中修改股數、平均成本或備註。改完後按下「儲存修改」。若要刪除持股，可以把股數改成 0 後儲存。</p>", unsafe_allow_html=True)
    edited = st.data_editor(
        portfolio,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "股票代號": st.column_config.TextColumn("股票代號", help="例如 AAPL、2330.TW"),
            "股數": st.column_config.NumberColumn("股數", min_value=0.0, step=1.0),
            "平均成本": st.column_config.NumberColumn("平均成本", min_value=0.0, step=1.0),
            "買入日期": st.column_config.TextColumn("買入日期", help="格式建議 YYYY-MM-DD"),
            "備註": st.column_config.TextColumn("備註"),
        },
        hide_index=True,
        key="portfolio_editor",
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("儲存修改"):
            save_portfolio(edited)
            st.success("已儲存持股紀錄。")
            st.rerun()
    with c2:
        uploaded = st.file_uploader("匯入持股 CSV", type=["csv"])
        if uploaded is not None:
            imported = pd.read_csv(uploaded)
            save_portfolio(imported)
            st.success("已匯入持股 CSV。")
            st.rerun()

with tab_allocation:
    st.markdown("### 資產配置")
    left, right = st.columns([.95, 1.05], gap="large")
    allocation_frame = snapshot[["股票代號", "目前市值（台幣)"]].copy() if False else snapshot[["股票代號", "目前市值（台幣）"]].copy()
    if cash_twd > 0:
        allocation_frame = pd.concat([allocation_frame, pd.DataFrame([{"股票代號": "現金", "目前市值（台幣）": cash_twd}])], ignore_index=True)
    with left:
        pie = px.pie(allocation_frame, values="目前市值（台幣）", names="股票代號", hole=.55, title="股票與現金配置")
        pie.update_traces(textposition="inside", textinfo="percent+label")
        pie = make_fig_dark(pie, 430)
        st.plotly_chart(pie, use_container_width=True)
    with right:
        bar = px.bar(snapshot.sort_values("持股占比"), x="持股占比", y="股票代號", orientation="h", title="各持股占比")
        bar.update_traces(marker_color="#45D39A")
        bar.update_xaxes(tickformat=".0%")
        bar = make_fig_dark(bar, 430)
        st.plotly_chart(bar, use_container_width=True)

    largest = snapshot.sort_values("持股占比", ascending=False).iloc[0]
    if largest["持股占比"] >= 0.35:
        st.markdown(
            f"<div class='warn'>提醒：{largest['股票代號']} 占比約 {pct(largest['持股占比'])}，單一持股比重偏高。若這檔股票大幅下跌，整體投資組合會受到明顯影響。</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div class='note'>目前最大單一持股占比未超過 35%，集中度相對可控。不過仍建議定期檢查是否過度集中在同一產業。</div>", unsafe_allow_html=True)

with tab_performance:
    st.markdown("### 績效追蹤")
    if len(series) < 3:
        st.info("資料筆數不足，暫時無法建立績效圖。")
    else:
        norm = series / series.iloc[0] * 100
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=norm.index, y=norm, name="我的投資組合", line=dict(color="#45D39A", width=2.8)))
        if benchmark and benchmark in prices.columns:
            bench = prices[benchmark].dropna()
            bench = bench.loc[bench.index >= norm.index.min()]
            if not bench.empty:
                fig.add_trace(go.Scatter(x=bench.index, y=bench / bench.iloc[0] * 100, name=f"比較基準 {benchmark}", line=dict(color="#E6C15C", width=2.2)))
        fig.update_layout(title="累積表現比較（起始值 100）", yaxis_title="指數化價值")
        fig = make_fig_dark(fig, 460)
        st.plotly_chart(fig, use_container_width=True)

        dd_fig = go.Figure()
        dd_fig.add_trace(go.Scatter(x=drawdown.index, y=drawdown, name="回撤", fill="tozeroy", line=dict(color="#F26D6D", width=2.4)))
        dd_fig.update_yaxes(tickformat=".0%")
        dd_fig.update_layout(title="歷史回撤走勢", yaxis_title="回撤幅度")
        dd_fig = make_fig_dark(dd_fig, 360)
        st.plotly_chart(dd_fig, use_container_width=True)

with tab_learn:
    st.markdown("### 新手說明")
    st.markdown(
        """
        <div class="panel">
        <h3>這些數字怎麼看？</h3>
        <p><b>目前總市值</b>：用最新股價乘上持有股數，並自動換算成台幣，代表目前持股約值多少新台幣。</p>
        <p><b>投入成本</b>：你買入時投入的本金，等於股數乘上平均成本。</p>
        <p><b>未實現損益</b>：目前市值減掉投入成本。還沒賣出之前，它只是帳面上的賺賠。</p>
        <p><b>總報酬率</b>：未實現損益除以投入成本，用來看整體賺賠比例。</p>
        <p><b>最大回撤</b>：從歷史高點到低點曾經跌多少。這個數字可以幫你想像最難熬的下跌幅度。</p>
        <p><b>夏普比率</b>：簡單說是「承擔一單位風險，換到多少報酬」。通常越高越好，但它不是唯一判斷標準。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="panel">
        <h3>給新手的使用建議</h3>
        <p>不要只看哪一檔賺最多，也要看它占你總資產多少。如果單一股票占比太高，投資組合會變得很依賴那一檔股票。</p>
        <p>如果你發現最大持股超過 35% 到 45%，可以思考是否需要分散到 ETF、不同產業或保留現金。</p>
        <p>這個工具不是投資建議，而是幫你整理自己的持股狀況，讓你更清楚知道目前承擔了什麼風險。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
