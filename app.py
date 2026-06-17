
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from data_utils import (
    generate_synthetic_workload_data, prepare_workload_data, apply_date_filter,
    team_capacity_summary, monthly_workload, simple_forecast, recommendations
)

st.set_page_config(page_title="Capacity & Workload Planning Intelligence", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.2rem;}

div[data-testid="stMetric"] {
    background:#f8fafc;
    border:1px solid #e5e7eb;
    padding:14px;
    border-radius:14px;
}

div[data-testid="stMetric"] label,
div[data-testid="stMetric"] div,
div[data-testid="stMetric"] p {
    color: #111827 !important;
}

.planner-note {
    border-left:4px solid #64748b;
    background:#f8fafc;
    color:#111827;
    padding:12px;
    border-radius:8px;
}

.planner-note * {
    color:#111827 !important;
}
</style>
""", unsafe_allow_html=True)


st.title("📊 Capacity & Workload Planning Intelligence")
st.caption("Workload demand, team capacity, utilization pressure, resource gaps, and planning scenarios.")

with st.sidebar:
    st.header("Data Source")
    uploaded = st.file_uploader("Upload workload CSV", type=["csv"])
    sample_size = st.slider("Synthetic rows", 500, 6000, 2500, step=500)

    if uploaded is not None:
        try:
            raw = pd.read_csv(uploaded)
            df = prepare_workload_data(raw)
            source = "Uploaded CSV"
        except Exception as e:
            st.error(f"Upload could not be processed: {e}")
            df = generate_synthetic_workload_data(sample_size)
            source = "Synthetic Demo"
    else:
        df = generate_synthetic_workload_data(sample_size)
        source = "Synthetic Demo"

    st.success(f"Source: {source}")
    st.divider()

    st.header("Time Filter")
    date_mode = st.selectbox("Select period", ["All Data", "Last 30 Days", "Last 90 Days", "Last 180 Days", "Custom Date Range"])
    custom_range = None
    if date_mode == "Custom Date Range":
        min_d = df["created_date"].min().date()
        max_d = df["created_date"].max().date()
        custom_range = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        if not isinstance(custom_range, tuple) or len(custom_range) != 2:
            custom_range = (min_d, max_d)

    fdf = apply_date_filter(df, date_mode, custom_range)
    
    st.divider()
    st.header("Focus Filter")

    team_options = ["All Teams"] + sorted(fdf["team"].dropna().unique().tolist())
    selected_team = st.selectbox("Team focus", team_options)

    if selected_team != "All Teams":
        fdf = fdf[fdf["team"] == selected_team]

    st.info(f"Records in view: {len(fdf):,}")


if fdf.empty:
    st.warning("No records available for the selected filter. Please widen the date range or upload a different dataset.")
    st.stop()

summary = team_capacity_summary(fdf)
monthly = monthly_workload(fdf)

tabs = st.tabs([
    "Command Center", "Workload Explorer", "Capacity Forecast",
    "Pressure Index", "Resource Gap", "Scenario Planner",
    "Recommendations", "Data Guide"
])

with tabs[0]:
    st.subheader("Planning Command Center")
    total = len(fdf)
    open_items = int(fdf["is_open"].sum())
    avg_util = float(summary["utilization_pct"].mean()) if not summary.empty else 0
    at_risk = int((summary["pressure_index"] >= 70).sum()) if not summary.empty else 0
    sla_breaches = int(fdf["sla_breached"].sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Work Items", f"{total:,}")
    c2.metric("Open Workload", f"{open_items:,}")
    c3.metric("Avg Utilization", f"{avg_util:.1f}%")
    c4.metric("At-Risk Teams", at_risk)
    c5.metric("SLA Breaches", f"{sla_breaches:,}")

    st.markdown("#### Team Capacity Overview")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        fig = px.bar(summary, x="team", y="pressure_index", title="Workload Pressure by Team", text="pressure_index")
        fig.update_layout(xaxis_title="", yaxis_title="Pressure Index")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.pie(fdf, names="status", title="Status Mix")
        st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader("Workload Explorer")
    left, right = st.columns(2)
    with left:
        stream = fdf.groupby("workstream").size().reset_index(name="work_items").sort_values("work_items", ascending=False)
        fig = px.bar(stream, x="workstream", y="work_items", title="Work Items by Workstream")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        pri = fdf.groupby("priority").size().reset_index(name="work_items")
        fig = px.bar(pri, x="priority", y="work_items", title="Priority Distribution")
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("#### Monthly Workload Trend")
    fig = px.line(monthly, x="created_date", y="work_items", markers=True, title="Work Items Over Time")
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.subheader("Capacity Forecast")
    horizon = st.slider("Forecast horizon in months", 3, 12, 6)
    fc = simple_forecast(monthly, horizon)
    hist = monthly[["created_date","work_items"]].rename(columns={"work_items":"value"})
    hist["series"] = "Actual"
    fplot = fc.rename(columns={"forecast_work_items":"value"})
    fplot["series"] = "Forecast"
    combined = pd.concat([hist, fplot[["created_date","value","series"]]], ignore_index=True)
    fig = px.line(combined, x="created_date", y="value", color="series", markers=True, title="Historical and Forecast Workload")
    st.plotly_chart(fig, use_container_width=True)
    if not fc.empty:
        st.info(f"Projected workload for next month: **{int(fc.iloc[0]['forecast_work_items']):,}** work items.")

with tabs[3]:
    st.subheader("Utilization & Workload Pressure Index")
    st.markdown('<div class="planner-note">The pressure index combines utilization, open workload, high-priority share, and SLA breach pressure.</div>', unsafe_allow_html=True)
    if summary.empty:
        st.warning("Not enough data to calculate pressure.")
    else:
        fig = px.scatter(summary, x="utilization_pct", y="pressure_index", size="work_items", hover_name="team", title="Utilization vs Pressure Index")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(summary[["team","work_items","open_items","utilization_pct","pressure_index","sla_breaches"]].head(10), use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Resource Gap Analysis")
    if summary.empty:
        st.warning("Not enough data to calculate resource gaps.")
    else:
        gap = summary.copy()
        gap["gap_type"] = np.where(gap["capacity_gap_hours"] > 0, "Deficit", "Surplus")
        fig = px.bar(gap, x="team", y="capacity_gap_hours", color="gap_type", title="Estimated Capacity Gap by Team")
        fig.update_layout(xaxis_title="", yaxis_title="Gap Hours")
        st.plotly_chart(fig, use_container_width=True)
        deficit = gap[gap["capacity_gap_hours"] > 0]["capacity_gap_hours"].sum()
        st.metric("Total Estimated Capacity Deficit", f"{deficit:,.0f} hours")

with tabs[5]:
    st.subheader("Scenario Planner")
    st.caption("Simulate demand and capacity changes to estimate planning pressure.")
    col1, col2, col3 = st.columns(3)
    demand_change = col1.slider("Demand change (%)", -40, 100, 20)
    capacity_change = col2.slider("Capacity change (%)", -40, 60, 0)
    productivity_change = col3.slider("Productivity improvement (%)", 0, 50, 10)
    scenario = summary.copy()
    scenario["scenario_demand_hours"] = scenario["total_estimated_hours"] * (1 + demand_change/100)
    scenario["scenario_capacity_hours"] = scenario["avg_capacity_hours"] * (1 + capacity_change/100) * (1 + productivity_change/100)
    scenario["scenario_gap_hours"] = scenario["scenario_demand_hours"] - scenario["scenario_capacity_hours"]
    scenario["scenario_utilization_pct"] = scenario["scenario_demand_hours"] / scenario["scenario_capacity_hours"].replace(0, np.nan) * 100
    c1, c2, c3 = st.columns(3)
    c1.metric("Scenario Demand Hours", f"{scenario['scenario_demand_hours'].sum():,.0f}")
    c2.metric("Scenario Capacity Hours", f"{scenario['scenario_capacity_hours'].sum():,.0f}")
    c3.metric("Net Gap Hours", f"{scenario['scenario_gap_hours'].sum():,.0f}")
    fig = px.bar(scenario, x="team", y="scenario_gap_hours", title="Scenario Capacity Gap by Team")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(scenario[["team","scenario_demand_hours","scenario_capacity_hours","scenario_gap_hours","scenario_utilization_pct"]].round(1), use_container_width=True, hide_index=True)

with tabs[6]:
    st.subheader("Planning Recommendations")
    for i, rec in enumerate(recommendations(summary), 1):
        st.markdown(f"**{i}. {rec}**")
    st.markdown("---")
    st.markdown("#### Suggested Management Actions")
    st.write("- Review high-pressure teams weekly.")
    st.write("- Rebalance lower-priority work away from overloaded teams.")
    st.write("- Use forecast outputs for short-term staffing or scheduling decisions.")
    st.write("- Track SLA breach patterns as early signals of capacity stress.")

with tabs[7]:
    st.subheader("Data Guide")
    st.markdown("""
This app accepts general workload, ticket, task, queue, or operational datasets.

**Recommended columns:** `created_date`, `team`, `workstream`, `priority`, `status`, `estimated_hours`, `actual_hours`, `capacity_hours`, `due_date`.

If some optional fields are missing, the app creates reasonable defaults so the dashboard remains usable.
    """)
    st.dataframe(fdf.head(50), use_container_width=True, hide_index=True)
