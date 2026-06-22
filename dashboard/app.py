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
    "insider": "#C084FC",  # roxo — informação privilegiada
    "options": "#FB923C",  # laranja — smart money flow
}

TYPE_EMOJI = {
    "analyst": "📈",
    "earnings": "💰",
    "product": "🚀",
    "macro": "🌐",
    "rotation": "🔄",
    "insider": "🕵️",
    "options": "🎯",
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

    all_types = ["analyst", "earnings", "product", "macro", "rotation", "insider", "options"]
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

    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
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
    # KPIs novos — insider e options
    insider_today = int(df_raw[df_raw["signal_type"] == "insider"]["date_only"].apply(
        lambda d: str(d)[:10] == datetime.now().strftime("%Y-%m-%d")
        if pd.notna(d) else False
    ).sum()) if "signal_type" in df_raw.columns and "date_only" in df_raw.columns else 0
    options_today = int(df_raw[df_raw["signal_type"] == "options"]["date_only"].apply(
        lambda d: str(d)[:10] == datetime.now().strftime("%Y-%m-%d")
        if pd.notna(d) else False
    ).sum()) if "signal_type" in df_raw.columns and "date_only" in df_raw.columns else 0
    c7.metric("🕵️ Insider buys", insider_today, help="Compras de insiders detectadas hoje")
    c8.metric("🎯 Options flow", options_today, help="Fluxo de opções incomum detectado hoje")
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

    # ── Insider Buying ─────────────────────────────────────────────────────
    insider_df = df[df["signal_type"] == "insider"].copy() if "signal_type" in df.columns else pd.DataFrame()
    options_df = df[df["signal_type"] == "options"].copy() if "signal_type" in df.columns else pd.DataFrame()

    if not insider_df.empty or not options_df.empty:
        st.divider()
        col_ins, col_opt = st.columns(2)

        with col_ins:
            st.subheader("🕵️ Insider Buying")
            if not insider_df.empty:
                ins_cols = [c for c in ["date_only", "ticker", "raw_score", "horizon", "headline", "outcome"] if c in insider_df.columns]
                ins_rename = {"date_only": "Data", "ticker": "Ticker", "raw_score": "Score", "horizon": "Horizonte", "headline": "Detalhe", "outcome": "Estado"}
                st.dataframe(
                    insider_df[ins_cols].rename(columns=ins_rename).sort_values("Score", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )
                # Gráfico de barras — insiders por ticker
                if "ticker" in insider_df.columns:
                    fig_ins = px.bar(
                        insider_df["ticker"].value_counts().reset_index(),
                        x="ticker",
                        y="count",
                        color_discrete_sequence=["#C084FC"],
                        title="Compras por ticker",
                    )
                    fig_ins.update_layout(margin=dict(t=30, b=10, l=0, r=0), height=200, showlegend=False, xaxis_title="", yaxis_title="Compras")
                    st.plotly_chart(fig_ins, use_container_width=True)
            else:
                st.caption("Nenhuma compra de insider no período com os filtros actuais.")

        with col_opt:
            st.subheader("🎯 Options Flow Incomum")
            if not options_df.empty:
                opt_cols = [c for c in ["date_only", "ticker", "raw_score", "horizon", "headline", "outcome"] if c in options_df.columns]
                opt_rename = {"date_only": "Data", "ticker": "Ticker", "raw_score": "Score", "horizon": "Horizonte", "headline": "Detalhe", "outcome": "Estado"}
                st.dataframe(
                    options_df[opt_cols].rename(columns=opt_rename).sort_values("Score", ascending=False),
                    use_container_width=True,
                    hide_index=True,
                )
                # Timeline de options flow
                if "date_only" in options_df.columns:
                    daily_opt = options_df.groupby("date_only").size().reset_index(name="count")
                    daily_opt["date_only"] = daily_opt["date_only"].astype(str)
                    fig_opt = px.bar(
                        daily_opt,
                        x="date_only",
                        y="count",
                        color_discrete_sequence=["#FB923C"],
                        title="Options flow por dia",
                    )
                    fig_opt.update_layout(margin=dict(t=30, b=10, l=0, r=0), height=200, showlegend=False, xaxis_title="", yaxis_title="Sinais")
                    st.plotly_chart(fig_opt, use_container_width=True)
            else:
                st.caption("Nenhum options flow incomum no período com os filtros actuais.")

        # Mega-convergência alert
        insider_tickers = set(insider_df["ticker"].dropna()) if not insider_df.empty and "ticker" in insider_df.columns else set()
        options_tickers = set(options_df["ticker"].dropna()) if not options_df.empty and "ticker" in options_df.columns else set()
        mega = insider_tickers & options_tickers
        if mega:
            st.markdown(
                f"""
                <div style='background: linear-gradient(135deg, #7c3aed, #ea580c);
                            padding: 16px 20px; border-radius: 10px; margin: 12px 0;'>
                    <h3 style='color: white; margin: 0 0 8px 0;'>⚡ MEGA-CONVERGÊNCIA DETECTADA</h3>
                    <p style='color: #fde68a; margin: 0; font-size: 18px; font-weight: bold;'>
                        {' &nbsp;·&nbsp; '.join(sorted(mega))}
                    </p>
                    <p style='color: #e2e8f0; margin: 8px 0 0 0; font-size: 13px;'>
                        Insiders a comprar E smart money em opções no mesmo ticker — sinal de máxima convicção.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Aprendizagem — Performance histórica ───────────────────────────────
    st.subheader("🧠 Aprendizagem do sistema")
    try:
        from core.performance_analyzer import load_cache
        perf = load_cache()
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.metric("Sinais fechados analisados", perf.get("total_closed", 0))
            if perf.get("sufficient_data"):
                ts = perf.get("generated_at", "")[:10]
                st.caption(f"Pesos adaptativos ACTIVOS — última análise: {ts}")
                st.success(f"Top fontes: {', '.join(perf.get('top_sources', [])) or '—'}")
                st.success(f"Top combinações: {', '.join(perf.get('top_combinations', [])) or '—'}")
            else:
                st.info(perf.get("notes", "A aguardar dados suficientes."))
        with col_p2:
            if perf.get("sufficient_data") and perf.get("by_type"):
                perf_rows = [
                    {"Tipo": k, "Hit Rate": f"{v['hit_rate']:.0%}", "P&L Médio": f"{v['avg_pnl']:+.1f}%", "Total": v["total"]}
                    for k, v in perf["by_type"].items()
                ]
                st.dataframe(pd.DataFrame(perf_rows), use_container_width=True, hide_index=True)
            else:
                st.caption("Tabela disponível após 10+ sinais fechados.")
    except Exception as e:
        st.caption(f"Performance cache indisponível: {e}")

    st.divider()

    # ── Backtest histórico ─────────────────────────────────────────────────
    st.subheader("🔬 Backtest — Casos históricos reais")
    st.caption("Eventos históricos documentados corridos pelo classificador e scorer do sistema, com P&L real via yfinance.")

    try:
        from core.backtest_engine import load_results
        bt_data = load_results()

        if not bt_data:
            st.info(
                "Nenhum backtest corrido ainda. Executa: `python -m scripts.run_backtest`"
            )
        else:
            bt_df = pd.DataFrame(bt_data)

            # KPIs do backtest
            total = len(bt_df)
            alerted = int((bt_df["would_alert"] == True).sum())
            kept = int((bt_df["would_keep"] == True).sum())
            hits = int((bt_df["hit"] == True).sum())
            decided = int(bt_df["hit"].notna().sum())
            hit_rate = hits / decided * 100 if decided > 0 else 0

            bc1, bc2, bc3, bc4 = st.columns(4)
            bc1.metric("Eventos testados", total)
            bc2.metric("🔴 Teria alertado", f"{alerted} ({alerted/total*100:.0f}%)")
            bc3.metric("🟡 Teria monitorizado", f"{kept} ({kept/total*100:.0f}%)")
            bc4.metric("✅ Taxa de acerto real", f"{hit_rate:.0f}%", help=f"{hits} HITs em {decided} com resultado")

            st.markdown("---")

            # Tabela principal
            show_cols = ["event_date", "ticker", "signal_type", "catalyst_strength",
                         "final_score", "would_alert", "horizon", "durability_12h",
                         "pnl_3d", "pnl_10d", "pnl_30d", "pnl_90d", "hit", "stopped"]
            show_cols = [c for c in show_cols if c in bt_df.columns]
            bt_display = bt_df[show_cols].copy()
            bt_display = bt_display.rename(columns={
                "event_date": "Data", "ticker": "Ticker", "signal_type": "Tipo",
                "catalyst_strength": "Strength", "final_score": "Score",
                "would_alert": "Alertaria?", "horizon": "Horizonte",
                "durability_12h": "12h OK?",
                "pnl_3d": "P&L 3d", "pnl_10d": "P&L 10d",
                "pnl_30d": "P&L 30d", "pnl_90d": "P&L 90d",
                "hit": "HIT?", "stopped": "STOP?",
            })

            def _pnl_color(val):
                if pd.isna(val):
                    return ""
                return "color: #00C851; font-weight:bold" if val > 0 else "color: #FF4444"

            def _hit_color(val):
                if val is True:
                    return "color: #00C851; font-weight:bold"
                if val is False:
                    return "color: #FF4444"
                return ""

            pnl_cols = [c for c in ["P&L 3d", "P&L 10d", "P&L 30d", "P&L 90d"] if c in bt_display.columns]
            fmt_bt = {c: "{:+.1f}%" for c in pnl_cols}
            styled_bt = bt_display.style.format(fmt_bt, na_rep="—")
            for c in pnl_cols:
                styled_bt = styled_bt.map(_pnl_color, subset=[c])
            for c in ["HIT?", "STOP?"]:
                if c in bt_display.columns:
                    styled_bt = styled_bt.map(_hit_color, subset=[c])

            st.dataframe(styled_bt, use_container_width=True, height=500)

            st.markdown("---")
            col_bt1, col_bt2 = st.columns(2)

            # Gráfico: Score vs P&L real (10d)
            with col_bt1:
                st.markdown("**Score do sistema vs P&L real (10 dias)**")
                if "pnl_10d" in bt_df.columns and "final_score" in bt_df.columns:
                    scatter_df = bt_df[["ticker", "final_score", "pnl_10d", "signal_type", "hit"]].dropna(subset=["pnl_10d"])
                    scatter_df["resultado"] = scatter_df["hit"].map({True: "HIT", False: "Miss/Stop"}).fillna("N/A")
                    fig_sc = px.scatter(
                        scatter_df,
                        x="final_score",
                        y="pnl_10d",
                        color="resultado",
                        text="ticker",
                        color_discrete_map={"HIT": "#00C851", "Miss/Stop": "#FF4444", "N/A": "#9E9E9E"},
                        labels={"final_score": "Score do sistema", "pnl_10d": "P&L real 10 dias (%)"},
                    )
                    fig_sc.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
                    fig_sc.add_hline(y=8, line_dash="dot", line_color="#00C851", opacity=0.4,
                                     annotation_text="threshold 10d")
                    fig_sc.update_traces(textposition="top center")
                    fig_sc.update_layout(margin=dict(t=10, b=10), height=320)
                    st.plotly_chart(fig_sc, use_container_width=True)

            # Gráfico: Hit rate por tipo
            with col_bt2:
                st.markdown("**Taxa de acerto por tipo de sinal (backtest)**")
                if "signal_type" in bt_df.columns and "hit" in bt_df.columns:
                    hr_bt = (
                        bt_df[bt_df["hit"].notna()]
                        .groupby("signal_type")
                        .apply(lambda g: pd.Series({
                            "hit_rate": (g["hit"] == True).mean() * 100,
                            "total": len(g),
                        }))
                        .reset_index()
                    )
                    if not hr_bt.empty:
                        hr_bt["emoji"] = hr_bt["signal_type"].map(TYPE_EMOJI).fillna("")
                        hr_bt["label"] = hr_bt["emoji"] + " " + hr_bt["signal_type"]
                        fig_hr = px.bar(
                            hr_bt,
                            x="label",
                            y="hit_rate",
                            color="hit_rate",
                            color_continuous_scale=["#FF4444", "#FFD700", "#00C851"],
                            range_color=[0, 100],
                            text="hit_rate",
                        )
                        fig_hr.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
                        fig_hr.update_layout(
                            margin=dict(t=10, b=10), height=320,
                            coloraxis_showscale=False,
                            xaxis_title="", yaxis_title="Hit rate (%)",
                        )
                        st.plotly_chart(fig_hr, use_container_width=True)

    except Exception as e:
        st.caption(f"Backtest indisponível: {e}")
