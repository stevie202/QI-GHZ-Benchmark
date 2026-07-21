"""Streamlit dashboard for the GHZ fidelity benchmark results log.

Run: py -3.12 -m streamlit run dashboard.py
Reads results.jsonl, written by qi_bell_benchmark.py on every run.
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from qiskit import QuantumCircuit

RESULTS_LOG = Path("results.jsonl")

# Fixed backend -> color mapping so a series always carries the same color,
# regardless of which backends are selected in the filter.
BACKEND_COLORS = {
    "QX emulator": "#2a78d6",
    "Tuna-5": "#eb6834",
    "Ry emulator": "#1baf7a",
    "Tuna-9": "#eda100",
    "Tuna-17": "#e87ba4",
}

st.set_page_config(page_title="QI GHZ Benchmark", layout="wide")


def load_results() -> pd.DataFrame:
    if not RESULTS_LOG.exists():
        return pd.DataFrame(columns=["timestamp", "backend", "n_qubits", "fidelity", "shots"])
    rows = [json.loads(line) for line in RESULTS_LOG.read_text().splitlines() if line.strip()]
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def ghz_circuit_figure(n: int = 3):
    """A representative GHZ circuit (H + a CNOT chain) for the explainer panel."""
    qc = QuantumCircuit(n, n)
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    qc.measure(range(n), range(n))
    return qc.draw(output="mpl")


def ideal_histogram_figure():
    """Illustrative (not measured) ideal outcome split — conceptual, not experiment data."""
    fig = go.Figure(
        go.Bar(
            x=["|00…0⟩", "|11…1⟩"],
            y=[0.5, 0.5],
            marker_color="#2a78d6",
            text=["50%", "50%"],
            textposition="outside",
            hovertemplate="%{x}<br>%{y:.0%} of shots<extra></extra>",
        )
    )
    fig.update_layout(
        title="Ideal (noiseless) outcome split",
        yaxis_title="Share of shots",
        yaxis_range=[0, 0.65],
        showlegend=False,
        height=320,
        margin=dict(t=40, b=10),
    )
    return fig


st.title("Quantum Inspire GHZ Fidelity Benchmark")
st.caption(
    'Run `py -3.12 qi_bell_benchmark.py "<backend>"` to add data — this page reads results.jsonl.'
)

df_all = load_results()

if df_all.empty:
    st.info("No results yet — run qi_bell_benchmark.py at least once to populate results.jsonl.")
    st.stop()

# --- About this experiment: summary + explainer graphics ---
st.subheader("About this experiment")
col_text, col_circuit, col_hist = st.columns([1.2, 1, 1])
with col_text:
    st.markdown(
        """
Each run entangles qubits into a **GHZ state** (a **Bell** state when n=2): a
Hadamard on qubit 0, then a chain of CNOTs cascading down the register. Ideally,
every measurement collapses to all-0s or all-1s — nothing in between.

**Fidelity** is the fraction of shots landing in one of those two outcomes.
On the QX emulator it stays close to 1.0. On real Tuna hardware it decays as
circuit size grows: limited qubit connectivity forces extra SWAP gates during
transpilation, and deeper circuits accumulate more noise.
        """
    )
with col_circuit:
    st.pyplot(ghz_circuit_figure(3))
    st.caption("3-qubit GHZ circuit (same pattern for any size)")
with col_hist:
    st.plotly_chart(ideal_histogram_figure(), use_container_width=True)

# --- At a glance: summary stats over the full logged history ---
best = df_all.loc[df_all["fidelity"].idxmax()]
worst = df_all.loc[df_all["fidelity"].idxmin()]
stat_cols = st.columns(5)
stat_cols[0].metric("Runs logged", df_all["timestamp"].nunique())
stat_cols[1].metric("Backends tested", df_all["backend"].nunique())
stat_cols[2].metric(f"Best fidelity ({best['backend']}, n={int(best['n_qubits'])})", f"{best['fidelity']:.3f}")
stat_cols[3].metric(f"Worst fidelity ({worst['backend']}, n={int(worst['n_qubits'])})", f"{worst['fidelity']:.3f}")
stat_cols[4].metric(
    "Last run",
    df_all["timestamp"].max().strftime("%b %d, %H:%M"),
    help=df_all["timestamp"].max().strftime("%Y-%m-%d %H:%M:%S UTC"),
)

st.divider()

backends_present = [b for b in BACKEND_COLORS if b in df_all["backend"].unique()]
selected = st.sidebar.multiselect("Backends", backends_present, default=backends_present)

df = df_all[df_all["backend"].isin(selected)]
if df.empty:
    st.warning("No backends selected.")
    st.stop()

show_legend = len(selected) > 1

# --- KPI row: latest fidelity at the largest tested size, per backend ---
st.subheader("Latest result per backend")
cols = st.columns(len(selected))
for col, backend in zip(cols, selected):
    sub = df[df["backend"] == backend]
    latest_run = sub[sub["timestamp"] == sub["timestamp"].max()]
    biggest = latest_run.loc[latest_run["n_qubits"].idxmax()]
    col.metric(f"{backend} (n={int(biggest['n_qubits'])})", f"{biggest['fidelity']:.3f}")

st.divider()

# --- Fidelity vs GHZ size, latest run per backend ---
st.subheader("Fidelity vs GHZ size (latest run per backend)")
fig1 = go.Figure()
for backend in selected:
    sub = df[df["backend"] == backend]
    latest_run = sub[sub["timestamp"] == sub["timestamp"].max()].sort_values("n_qubits")
    fig1.add_trace(
        go.Scatter(
            x=latest_run["n_qubits"],
            y=latest_run["fidelity"],
            mode="lines+markers",
            name=backend,
            line=dict(color=BACKEND_COLORS[backend], width=2),
            marker=dict(size=8),
            hovertemplate=f"{backend}<br>n=%{{x}} qubits<br>fidelity=%{{y:.3f}}<extra></extra>",
        )
    )
fig1.add_hline(y=1.0, line_dash="dash", line_color="grey")
fig1.update_layout(
    xaxis_title="GHZ state size (qubits)",
    yaxis_title="Fidelity",
    yaxis_range=[0, 1.05],
    legend_title_text="Backend",
    showlegend=show_legend,
    height=450,
)
st.plotly_chart(fig1, use_container_width=True)

# --- Fidelity over time, one series per backend at its largest tested size ---
st.subheader("Fidelity over time (largest GHZ size tested per backend)")
fig2 = go.Figure()
for backend in selected:
    sub = df[df["backend"] == backend]
    n_max = sub["n_qubits"].max()
    trend = sub[sub["n_qubits"] == n_max].sort_values("timestamp")
    fig2.add_trace(
        go.Scatter(
            x=trend["timestamp"],
            y=trend["fidelity"],
            mode="lines+markers",
            name=f"{backend} (n={n_max})",
            line=dict(color=BACKEND_COLORS[backend], width=2),
            marker=dict(size=7),
            hovertemplate=f"{backend}<br>%{{x}}<br>fidelity=%{{y:.3f}}<extra></extra>",
        )
    )
fig2.add_hline(y=1.0, line_dash="dash", line_color="grey")
fig2.update_layout(
    xaxis_title="Run time",
    yaxis_title="Fidelity",
    yaxis_range=[0, 1.05],
    legend_title_text="Backend",
    showlegend=show_legend,
    height=450,
)
st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Raw results")
st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)
