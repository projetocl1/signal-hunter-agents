"""
Signal Hunter — Dashboard principal.

Execução:
    streamlit run dashboard/app.py
"""
from __future__ import annotations

import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Garantir que o directório raiz do projecto está no sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from dashboard.data import compute_kpis, load_signals  # noqa: E402

# ── PWA — instalar como app no tablet/telemóvel ────────────────────────────
_SVG_ICON = base64.b64encode(b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="90" fill="#0f1117"/>
  <rect x="80" y="300" width="60" height="140" rx="8" fill="#4285F4"/>
  <rect x="180" y="220" width="60" height="220" rx="8" fill="#4285F4"/>
  <rect x="280" y="150" width="60" height="290" rx="8" fill="#00C851"/>
  <rect x="380" y="80"  width="60" height="360" rx="8" fill="#00C851"/>
  <polyline points="110,310 210,230 310,160 410,90"
            stroke="#FFD700" stroke-width="18" fill="none"
            stroke-linecap="round" stroke-linejoin="round"/>
  <polygon points="390,60 440,110 410,90" fill="#FFD700"/>
</svg>
""".strip()).decode()

_MANIFEST = base64.b64encode(json.dumps({
    "name": "Signal Hunter",
    "short_name": "Signals",
    "description": "Dashboard de catalisadores de mercado",
    "icons": [
        {"src": f"data:image/svg+xml;base64,{_SVG_ICON}", "sizes": "512x512",
         "type": "image/svg+xml", "purpose": "any maskable"},
    ],
    "start_url": ".",
    "display": "standalone",
    "theme_color": "#0f1117",
    "background_color": "#0f1117",
    "orientation": "portrait-primary",
}).encode()).decode()


def _inject_pwa() -> None:
    """Injeta manifesto PWA e meta tags Apple no <head> da página."""
    icon_url = f"data:image/svg+xml;base64,{_SVG_ICON}"
    manifest_url = f"data:application/manifest+json;base64,{_MANIFEST}"
    components.html(f"""
    <script>
    (function() {{
        var h = window.parent.document.head;
        if (h.querySelector('link[rel="manifest"]')) return;  // já injectado
        var lm = document.createElement('link');
        lm.rel = 'manifest'; lm.href = '{manifest_url}';
        h.appendChild(lm);
        var lt = document.createElement('link');
        lt.rel = 'apple-touch-icon'; lt.href = '{icon_url}';
        h.appendChild(lt);
        [
            ['apple-mobile-web-app-capable',        'yes'],
            ['apple-mobile-web-app-title',          'Signal Hunter'],
            ['apple-mobile-web-app-status-bar-style','black-translucent'],
            ['mobile-web-app-capable',              'yes'],
            ['theme-color',                         '#0f1117'],
        ].forEach(function(m) {{
            var el = document.createElement('meta');
            el.name = m[0]; el.content = m[1];
            h.appendChild(el);
        }});
    }})();
    </script>
    """, height=0, scrolling=False)

# ── Paleta de cores ────────────────────────────────────────────────────────
OUTCOME_COLORS = {
    "hit": "#00C851",
    "open": "#4285F4",
    "stopped": "#FF4444",
    "expired": "#9E9E9E",
}
TYPE_COLORS = {
    "analyst": "#4285F4",
    "earnings": "#FF6B6B",
    "product": "#4ECDC4",
    "macro": "#FFE66D",
    "rotation": "#A8E6CF",
}

# ── Configuração da página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Signal Hunter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

_inject_pwa()

st.markdown(
    """
    <style>
    .metric-label { font-size: 13px !important; color: #888 !important; }
    .stMetric > div { border-radius: 8px; padding: 8px; background: #1e1e2e; }
    div[data-testid="stMetricDelta"] { font-size: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar — Filtros ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎯 Signal Hunter")
    st.caption("Dashboard de acompanhamento de sinais")
    st.divider()

    days = st.slider("Período (dias)", min_value=7, max_value=90, value=30, step=7)
    min_score = st.slider("Score mínimo", min_value=0, max_value=13, value=0)

    all_types = ["analyst", "earnings", "product", "macro", "rotation"]
    sel_types = st.multiselect("Tipos de sinal", all_types, default=all_types)

    all_horizons = ["3d", "10d", "30d", "90d"]
    sel_horizons = st.multiselect("Horizonte", all_horizons, default=all_horizons)

    all_outcomes = ["open", "hit", "stopped", "expired"]
    sel_outcomes = st.multiselect("Estado", all_outcomes, default=all_outcomes)

    st.divider()
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Cache: {int(os.environ.get('DASHBOARD_CACHE_TTL', 3600)) // 60} min")

# ── Carregar dados ─────────────────────────────────────────────────────────
with st.spinner("A carregar dados do Airtable..."):
    try:
        df_raw = load_signals(days)
        data_ok = True
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        data_ok = False
        df_raw = pd.DataFrame()

# ── Aplicar filtros ────────────────────────────────────────────────────────
if data_ok and not df_raw.empty:
    df = df_raw.copy()
    if "raw_score" in df.columns:
        df = df[df["raw_score"] >= min_score]
    if "signal_type" in df.columns and sel_types:
        df = df[df["signal_type"].isin(sel_types)]
    if "horizon" in df.columns and sel_horizons:
        df = df[df["horizon"].isin(sel_horizons)]
    if "outcome" in df.columns and sel_outcomes:
        df = df[df["outcome"].isin(sel_outcomes)]
else:
    df = pd.DataFrame()

# ── Cabeçalho ─────────────────────────────────────────────────────────────
col_title, col_time = st.columns([3, 1])
with col_title:
    st.title("🎯 Signal Hunter — Dashboard")
with col_time:
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.divider()

# ── KPIs ───────────────────────────────────────────────────────────────────
if not df_raw.empty:
    kpi = compute_kpis(df_raw)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📅 Sinais hoje", kpi["sinais_hoje"])
    c2.metric(
        "🔴 Alta prioridade",
        kpi["alta_prioridade_hoje"],
        help="Score ≥ 8 detectados hoje",
    )
    c3.metric("📂 Posições abertas", kpi["posicoes_abertas"])
    c4.metric(
        "✅ Taxa de acerto",
        f"{kpi['hit_rate_pct']:.1f}%",
        help="Hit / (Hit + Stopped + Expired)",
    )
    c5.metric(
        "💰 P&L médio",
        f"{kpi['avg_pnl_pct']:+.2f}%",
        delta_color="normal",
        help="Posições fechadas",
    )
    c6.metric(
        "🔀 Convergências",
        kpi["convergencias_ativas"],
        help="Posições abertas com convergência detectada",
    )
else:
    st.info("Sem dados para o período seleccionado. Verifica as credenciais do Airtable no .env")

st.divider()

# ── Gráficos — linha 1 ─────────────────────────────────────────────────────
if not df.empty:
    col_a, col_b, col_c = st.columns(3)

    # Donut — sinais por tipo
    with col_a:
        st.subheader("Sinais por tipo")
        if "signal_type" in df.columns:
            counts = df["signal_type"].value_counts().reset_index()
            counts.columns = ["tipo", "count"]
            fig = px.pie(
                counts,
                names="tipo",
                values="count",
                hole=0.5,
                color="tipo",
                color_discrete_map=TYPE_COLORS,
            )
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=260, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

    # Bar — score médio por fonte
    with col_b:
        st.subheader("Score médio por fonte")
        if "source" in df.columns and "raw_score" in df.columns:
            src = (
                df.groupby("source")["raw_score"]
                .agg(["mean", "count"])
                .reset_index()
                .sort_values("mean", ascending=True)
            )
            src.columns = ["source", "score_medio", "count"]
            fig = px.bar(
                src,
                x="score_medio",
                y="source",
                orientation="h",
                text="count",
                color="score_medio",
                color_continuous_scale="Blues",
            )
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=260,
                coloraxis_showscale=False,
                xaxis_title="Score médio",
                yaxis_title="",
            )
            fig.update_traces(texttemplate="%{text} sinais", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    # Bar — outcomes
    with col_c:
        st.subheader("Estados das posições")
        outcome_counts = df["outcome"].value_counts().reset_index()
        outcome_counts.columns = ["estado", "count"]
        fig = px.bar(
            outcome_counts,
            x="estado",
            y="count",
            color="estado",
            color_discrete_map=OUTCOME_COLORS,
            text="count",
        )
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=260,
            showlegend=False,
            xaxis_title="",
            yaxis_title="Sinais",
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Linha temporal ──────────────────────────────────────────────────────
    st.subheader("📈 Sinais por dia")
    if "date_only" in df.columns:
        daily = df.groupby(["date_only", "outcome"]).size().reset_index(name="count")
        daily["date_only"] = daily["date_only"].astype(str)  # evitar eixo com horas
        fig = px.bar(
            daily,
            x="date_only",
            y="count",
            color="outcome",
            color_discrete_map=OUTCOME_COLORS,
            barmode="stack",
        )
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=220,
            xaxis_title="Data",
            yaxis_title="Sinais",
            legend_title="Estado",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Performance por horizonte e tipo ───────────────────────────────────
    col_d, col_e = st.columns(2)

    with col_d:
        st.subheader("Taxa de acerto por horizonte")
        closed = df[df["outcome"].isin(["hit", "stopped", "expired"])]
        if "horizon" in closed.columns and not closed.empty:
            hr = (
                closed.groupby("horizon")
                .apply(lambda g: pd.Series({
                    "hit_rate": (g["outcome"] == "hit").mean() * 100,
                    "total": len(g),
                }))
                .reset_index()
            )
            fig = px.bar(
                hr,
                x="horizon",
                y="hit_rate",
                text="hit_rate",
                color="hit_rate",
                color_continuous_scale=["#FF4444", "#FFD700", "#00C851"],
                range_color=[0, 100],
            )
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=240,
                coloraxis_showscale=False,
                xaxis_title="Horizonte",
                yaxis_title="Taxa de acerto (%)",
            )
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Sem posições fechadas suficientes.")

    with col_e:
        st.subheader("Distribuição de P&L (posições fechadas)")
        closed_pnl = df[df["outcome"].isin(["hit", "stopped", "expired"])]
        if "pnl_pct" in closed_pnl.columns and not closed_pnl.empty and not closed_pnl["pnl_pct"].isna().all():
            fig = px.histogram(
                closed_pnl,
                x="pnl_pct",
                nbins=20,
                color="outcome",
                color_discrete_map=OUTCOME_COLORS,
                barmode="overlay",
                opacity=0.8,
            )
            fig.add_vline(x=0, line_dash="dash", line_color="white", opacity=0.5)
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=240,
                xaxis_title="P&L (%)",
                yaxis_title="Sinais",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Sem P&L registado em posições fechadas.")

    st.divider()

    # ── Tabela — Posições Abertas ──────────────────────────────────────────
    st.subheader("📂 Posições abertas")
    open_pos = df[df["outcome"] == "open"].copy()
    if not open_pos.empty:
        display_cols = [c for c in ["ticker", "signal_type", "raw_score", "horizon", "convergence", "entry_price", "price_now", "pnl_pct", "date_only"] if c in open_pos.columns]
        rename = {
            "ticker": "Ticker",
            "signal_type": "Tipo",
            "raw_score": "Score",
            "horizon": "Horizonte",
            "convergence": "Convergência",
            "entry_price": "Entrada ($)",
            "price_now": "Atual ($)",
            "pnl_pct": "P&L (%)",
            "date_only": "Data",
        }
        tbl = open_pos[display_cols].rename(columns=rename)

        def _color_pnl(val):
            if pd.isna(val):
                return ""
            return "color: #00C851" if val > 0 else ("color: #FF4444" if val < 0 else "")

        def _color_conv(val):
            return "color: #FFD700; font-weight: bold" if val else ""

        fmt = {}
        if "P&L (%)" in tbl.columns:
            fmt["P&L (%)"] = "{:+.2f}%"
        if "Entrada ($)" in tbl.columns:
            fmt["Entrada ($)"] = "{:.2f}"
        if "Atual ($)" in tbl.columns:
            fmt["Atual ($)"] = "{:.2f}"

        styled = tbl.style.format(fmt, na_rep="—")
        if "P&L (%)" in tbl.columns:
            styled = styled.map(_color_pnl, subset=["P&L (%)"])
        if "Convergência" in tbl.columns:
            styled = styled.map(_color_conv, subset=["Convergência"])

        st.dataframe(styled, use_container_width=True, height=min(400, (len(tbl) + 1) * 35 + 38))
    else:
        st.caption("Sem posições abertas com os filtros actuais.")

    st.divider()

    # ── Tabela — Todos os sinais ────────────────────────────────────────────
    st.subheader(f"🗂️ Todos os sinais ({len(df)} registos)")
    all_cols = [c for c in ["date_only", "ticker", "signal_type", "raw_score", "horizon", "outcome", "convergence", "pnl_pct", "headline"] if c in df.columns]
    rename_all = {
        "date_only": "Data", "ticker": "Ticker", "signal_type": "Tipo",
        "raw_score": "Score", "horizon": "Horizonte", "outcome": "Estado",
        "convergence": "Conv.", "pnl_pct": "P&L (%)", "headline": "Título",
    }
    tbl_all = df[all_cols].rename(columns=rename_all)
    fmt_all = {}
    if "P&L (%)" in tbl_all.columns:
        fmt_all["P&L (%)"] = "{:+.2f}%"
    st.dataframe(
        tbl_all.style.format(fmt_all, na_rep="—"),
        use_container_width=True,
        height=400,
    )
