import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Ações BR 2025", page_icon="📈", layout="wide")

TICKERS = {"PETR4": "PETR4.SA", "ITUB4": "ITUB4.SA", "VALE3": "VALE3.SA"}
COLORS = {"PETR4": "#009B3A", "ITUB4": "#003087", "VALE3": "#0066CC"}

YEAR_START = date(2025, 1, 1)
YEAR_END = date(2025, 12, 31)

@st.cache_data(ttl=3600)
def load_full_year() -> tuple:
    raw = yf.download(list(TICKERS.values()), start=str(YEAR_START), end=str(YEAR_END), auto_adjust=True)
    close = raw["Close"].copy()
    close.columns = [c.replace(".SA", "") for c in close.columns]
    volume = raw["Volume"].copy()
    volume.columns = [c.replace(".SA", "") for c in volume.columns]
    return close, volume


st.title("📈 Performance de Ações — 2025")
st.caption("PETR4 · ITUB4 · VALE3 — dados da B3 via Yahoo Finance")

close_full, volume_full = load_full_year()
close_full = close_full.dropna(how="all")
last_available = close_full.index[-1].date() if len(close_full) > 0 else YEAR_END
first_available = close_full.index[0].date() if len(close_full) > 0 else YEAR_START

with st.sidebar:
    st.header("Filtros")
    start_date = st.date_input("Data inicial", value=first_available, min_value=first_available, max_value=last_available)
    end_date = st.date_input("Data final", value=last_available, min_value=first_available, max_value=last_available)
    st.divider()
    st.subheader("Ações exibidas")
    selected = {ticker: st.checkbox(ticker, value=True) for ticker in TICKERS}
    active = [t for t, v in selected.items() if v]

if not active:
    st.warning("Selecione ao menos uma ação na sidebar.")
    st.stop()

if start_date >= end_date:
    st.error("A data inicial deve ser anterior à data final.")
    st.stop()

mask = (close_full.index.date >= start_date) & (close_full.index.date <= end_date)
close = close_full.loc[mask, active].dropna(how="all")
volume = volume_full.loc[mask, active].dropna(how="all")

# --- Métricas resumidas ---
st.subheader("Resumo do período")
cols = st.columns(len(active))
for i, ticker in enumerate(active):
    s = close[ticker].dropna()
    if len(s) < 2:
        continue
    retorno = (s.iloc[-1] / s.iloc[0] - 1) * 100
    preco_atual = s.iloc[-1]
    vol_anual = s.pct_change().std() * (252 ** 0.5) * 100
    delta_str = f"{retorno:+.2f}%"
    cols[i].metric(
        label=ticker,
        value=f"R$ {preco_atual:.2f}",
        delta=delta_str,
        help=f"Volatilidade anualizada: {vol_anual:.1f}%",
    )
    cols[i].caption(f"Volatilidade anualizada: {vol_anual:.1f}%")

st.divider()

# --- Abas de gráficos ---
tab1, tab2, tab3, tab4 = st.tabs(["Preço Histórico", "Performance Comparativa", "Volume Negociado", "Volatilidade"])

with tab1:
    fig = go.Figure()
    for ticker in active:
        s = close[ticker].dropna()
        fig.add_trace(go.Scatter(x=s.index, y=s.values, name=ticker, line=dict(color=COLORS[ticker], width=2)))
    fig.update_layout(title="Preço de Fechamento (R$)", xaxis_title="Data", yaxis_title="Preço (R$)", hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = go.Figure()
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    for ticker in active:
        s = close[ticker].dropna()
        if len(s) == 0:
            continue
        perf = (s / s.iloc[0] - 1) * 100
        fig.add_trace(go.Scatter(x=perf.index, y=perf.values, name=ticker, line=dict(color=COLORS[ticker], width=2)))
    fig.update_layout(title="Retorno Acumulado (base 0% no início do período)", xaxis_title="Data", yaxis_title="Retorno (%)", hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    vol_long = volume[active].reset_index().melt(id_vars="Date", var_name="Ação", value_name="Volume")
    color_map = {t: COLORS[t] for t in active}
    fig = px.bar(vol_long, x="Date", y="Volume", color="Ação", barmode="group", color_discrete_map=color_map, title="Volume Diário Negociado", height=500)
    fig.update_layout(xaxis_title="Data", yaxis_title="Volume")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    fig = go.Figure()
    for ticker in active:
        s = close[ticker].dropna()
        vol_roll = s.pct_change().rolling(21).std() * (252 ** 0.5) * 100
        fig.add_trace(go.Scatter(x=vol_roll.index, y=vol_roll.values, name=ticker, line=dict(color=COLORS[ticker], width=2)))
    fig.update_layout(title="Volatilidade Anualizada — Janela Móvel 21 dias (%)", xaxis_title="Data", yaxis_title="Volatilidade (%)", hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)
