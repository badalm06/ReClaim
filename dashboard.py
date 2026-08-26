import streamlit as st
import pandas as pd
from pathlib import Path
from pipeline import run_pipeline
from audit.logger import init_db, get_all_logs, clear_logs

st.set_page_config(
    page_title="Reclaim",
    page_icon="💸",
    layout="wide"
)

# ── session state defaults ────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Upload & Configure"
if "pipeline_done" not in st.session_state:
    st.session_state.pipeline_done = False
if "summary" not in st.session_state:
    st.session_state.summary = {}

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💸 Reclaim")
    st.markdown("*Multi-agent revenue recovery*")
    st.divider()

    pages = ["Upload & Configure", "Live Pipeline", "Results Dashboard"]
    for p in pages:
        if st.button(p, key=f"nav_{p}", use_container_width=True,
                     type="primary" if st.session_state.page == p else "secondary"):
            st.session_state.page = p
            st.rerun()

    st.divider()
    st.caption("Razorpay Hackathon 2026 · Track 03")

page = st.session_state.page

# ── formatting helpers ────────────────────────────────────────────────────────
def fmt_inr(val):
    try:
        return f"₹{int(val):,}"
    except:
        return val

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — Upload & Configure
# ══════════════════════════════════════════════════════════════════════════════
if page == "Upload & Configure":
    st.title("Upload & Configure")
    st.markdown("Load the failed payment batch and review before running the pipeline.")
    st.divider()

    DATA_PATH = Path(__file__).parent / "data" / "razorpay_failed_payments.csv"
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Records",       len(df))
        col2.metric("Revenue at Risk",     f"₹{int(df['amount_inr'].sum()):,}")
        col3.metric("High Potential",      len(df[df["recovery_potential"] == "high"]))
        col4.metric("Permanently Blocked", int(df["permanently_blocked"].sum()))

        st.divider()
        st.subheader("Batch Preview")

        filter_type = st.selectbox(
            "Filter by failure type",
            ["All"] + sorted(df["failure_type"].unique().tolist())
        )
        preview_df = df if filter_type == "All" else df[df["failure_type"] == filter_type]

        display_df = preview_df[[
            "event_id", "customer_name", "amount_inr", "failure_reason",
            "failure_type", "recovery_potential", "retry_count", "permanently_blocked"
        ]].copy()
        display_df["amount_inr"] = display_df["amount_inr"].apply(fmt_inr)

        st.dataframe(display_df, use_container_width=True, height=380)

        st.divider()
        if st.button("▶ Run Pipeline", type="primary"):
            st.session_state.page        = "Live Pipeline"
            st.session_state.pipeline_done = False
            st.rerun()
    else:
        st.error("CSV not found. Place `razorpay_failed_payments.csv` in the `/data` folder.")

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — Live Pipeline
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Live Pipeline":
    st.title("Live Pipeline")
    st.markdown("Watch the agents process each record in real time.")
    st.divider()

    if not st.session_state.pipeline_done:
        progress_bar = st.progress(0)
        status_text  = st.empty()
        live_log     = st.empty()
        log_rows     = []

        def progress_callback(current, total, row, outcome):
            progress_bar.progress(current / total)
            status_text.markdown(
                f"**Processing [{current}/{total}]** — `{row['event_id']}` · {row['failure_reason']}"
            )
            icon = {"recovered": "🟢", "failed": "🔴", "unrecoverable": "⚫", "escalated": "🟡"}.get(outcome, "⚪")
            log_rows.append(f"{icon} `{row['event_id']}` · **{row['failure_reason']}** → {outcome}")
            live_log.markdown("\n\n".join(log_rows[-12:]))

        with st.spinner("Agents running..."):
            summary = run_pipeline(progress_callback=progress_callback)

        st.session_state.summary       = summary
        st.session_state.pipeline_done = True

        progress_bar.progress(1.0)
        status_text.markdown("✅ **Pipeline complete!**")
        st.divider()
        st.success(
            f"Processed {summary['total']} records · "
            f"₹{int(summary['total_recovered']):,} recovered · "
            f"{summary['recovery_rate']}% recovery rate"
        )
        if st.button("View Results →", type="primary"):
            st.session_state.page = "Results Dashboard"
            st.rerun()
    else:
        st.success("Pipeline already ran.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶ Run Again", type="secondary"):
                st.session_state.pipeline_done = False
                st.rerun()
        with col2:
            if st.button("View Results →", type="primary"):
                st.session_state.page = "Results Dashboard"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 3 — Results Dashboard
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Results Dashboard":
    st.title("Results Dashboard")
    st.divider()

    DB_PATH = Path(__file__).parent / "audit" / "audit.db"
    if not DB_PATH.exists():
        st.warning("No results yet. Run the pipeline first.")
        if st.button("Go to Pipeline →"):
            st.session_state.page = "Live Pipeline"
            st.rerun()
    else:
        init_db()
        cols, rows = get_all_logs()
        logs_df = pd.DataFrame(rows, columns=cols)

        summary         = st.session_state.summary
        total           = summary.get("total",           len(logs_df))
        n_recovered     = summary.get("recovered",       int((logs_df["outcome"] == "recovered").sum()))
        n_unrecoverable = summary.get("unrecoverable",   int((logs_df["outcome"] == "unrecoverable").sum()))
        n_escalated     = summary.get("escalated",       int((logs_df["outcome"] == "escalated").sum()))
        total_recovered = summary.get("total_recovered", float(logs_df[logs_df["outcome"] == "recovered"]["amount_recovered"].sum()))
        recovery_rate   = summary.get("recovery_rate",   round((n_recovered / total) * 100, 1) if total else 0)

        # ── metric cards ──
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Processed",  total)
        c2.metric("Recovered",        f"{n_recovered} ({recovery_rate}%)", delta=f"₹{int(total_recovered):,}")
        c3.metric("Unrecoverable",    n_unrecoverable)
        c4.metric("Escalated",        n_escalated)

        st.divider()

        # ── chart ──
        st.subheader("Recovery by failure type")
        chart_data    = logs_df.groupby(["failure_reason", "outcome"]).size().unstack(fill_value=0)
        outcome_order = [o for o in ["recovered", "failed", "unrecoverable", "escalated"] if o in chart_data.columns]
        st.bar_chart(chart_data[outcome_order], use_container_width=True, height=300)

        st.divider()

        # ── audit trail ──
        st.subheader("Audit Trail")
        fa, fb, fc = st.columns(3)
        filter_agent   = fa.selectbox("Agent",   ["All"] + sorted(logs_df["agent"].unique().tolist()))
        filter_outcome = fb.selectbox("Outcome", ["All"] + sorted(logs_df["outcome"].unique().tolist()))
        show_graceful  = fc.checkbox("Graceful failures only", value=False)

        filtered = logs_df.copy()
        if filter_agent   != "All":
            filtered = filtered[filtered["agent"]   == filter_agent]
        if filter_outcome != "All":
            filtered = filtered[filtered["outcome"] == filter_outcome]
        if show_graceful:
            filtered = filtered[
                (filtered["outcome"] == "unrecoverable") &
                (filtered["reason"].str.contains("blocked|expired|max retries", case=False, na=False))
            ]

        # ── format columns cleanly ──
        display_df = filtered[[
            "event_id", "customer_name", "amount_inr", "failure_reason",
            "agent", "action", "outcome", "amount_recovered", "reason", "timestamp"
        ]].copy()
        display_df["amount_inr"]       = display_df["amount_inr"].apply(fmt_inr)
        display_df["amount_recovered"] = display_df["amount_recovered"].apply(
            lambda x: fmt_inr(x) if x > 0 else "—"
        )

        def highlight_graceful(row):
            if row["outcome"] == "unrecoverable" and any(
                kw in str(row["reason"]).lower()
                for kw in ["blocked", "expired", "max retries"]
            ):
                return ["background-color: #2a2410"] * len(row)
            return [""] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_graceful, axis=1),
            use_container_width=True,
            height=420
        )
        st.caption("🔴 Highlighted rows = graceful failures (agent stopped, reason logged)")