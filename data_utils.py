
import numpy as np
import pandas as pd

TEAM_NAMES = ["Assessment Ops", "Content QA", "Learner Support", "Platform Support", "Review Team", "Project Delivery"]
WORKSTREAMS = ["Review", "Support Ticket", "Content Update", "Quality Check", "Escalation", "Documentation", "Implementation"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
STATUSES = ["Open", "In Progress", "Resolved", "Closed"]

def generate_synthetic_workload_data(n_rows: int = 2500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end = pd.Timestamp.today().normalize()
    start = end - pd.Timedelta(days=365)
    dates = pd.to_datetime(rng.choice(pd.date_range(start, end, freq="D"), size=n_rows))
    teams = rng.choice(TEAM_NAMES, size=n_rows, p=[0.18, 0.16, 0.20, 0.14, 0.17, 0.15])
    streams = rng.choice(WORKSTREAMS, size=n_rows)
    priority = rng.choice(PRIORITIES, size=n_rows, p=[0.28, 0.45, 0.22, 0.05])
    status = rng.choice(STATUSES, size=n_rows, p=[0.22, 0.26, 0.30, 0.22])
    priority_multiplier = pd.Series(priority).map({"Low":0.8, "Medium":1.0, "High":1.6, "Critical":2.2}).values
    estimated = np.round(np.maximum(0.5, rng.gamma(2.2, 3.0, size=n_rows) * priority_multiplier), 1)
    actual = np.round(np.maximum(0.5, estimated * rng.normal(1.08, 0.25, size=n_rows)), 1)
    team_capacity_map = {"Assessment Ops":420,"Content QA":360,"Learner Support":390,"Platform Support":310,"Review Team":340,"Project Delivery":370}
    capacity = pd.Series(teams).map(team_capacity_map).values + rng.normal(0, 25, size=n_rows)
    due_days = rng.choice([3, 5, 7, 10, 14, 21], size=n_rows, p=[0.08,0.18,0.30,0.22,0.16,0.06])
    due_date = dates + pd.to_timedelta(due_days, unit="D")
    closed_offset = rng.integers(1, 25, size=n_rows)
    closed_date = pd.Series(dates + pd.to_timedelta(closed_offset, unit="D"))
    closed_date = closed_date.where(pd.Series(status).isin(["Resolved","Closed"]), pd.NaT)
    df = pd.DataFrame({
        "work_id": [f"WK-{i+10000}" for i in range(n_rows)],
        "created_date": dates,
        "closed_date": closed_date,
        "team": teams,
        "workstream": streams,
        "priority": priority,
        "status": status,
        "estimated_hours": estimated,
        "actual_hours": actual,
        "capacity_hours": np.round(np.maximum(180, capacity), 1),
        "due_date": due_date,
    })
    return prepare_workload_data(df)

def _first_existing(df, candidates):
    lower_map = {c.lower().strip(): c for c in df.columns}
    for name in candidates:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None

def prepare_workload_data(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    mappings = {
        "created_date": ["created_date","date","created","submitted_date","opened_at","request_date","ticket_date","start_date"],
        "closed_date": ["closed_date","resolved_date","completed_date","closed","end_date","resolution_date"],
        "team": ["team","department","group","owner_team","assigned_team","unit","function"],
        "workstream": ["workstream","category","type","queue","issue_type","task_type","service_area"],
        "priority": ["priority","severity","urgency"],
        "status": ["status","state","ticket_status"],
        "estimated_hours": ["estimated_hours","estimate","estimated_effort","planned_hours","effort_hours"],
        "actual_hours": ["actual_hours","actual_effort","spent_hours","logged_hours"],
        "capacity_hours": ["capacity_hours","capacity","available_hours","team_capacity"],
        "due_date": ["due_date","sla_due_date","target_date","deadline"],
        "work_id": ["work_id","ticket_id","issue_id","id","task_id","request_id"],
    }
    rename_map = {}
    for std, cands in mappings.items():
        col = _first_existing(df, cands)
        if col:
            rename_map[col] = std
    df = df.rename(columns=rename_map)
    n = len(df)
    rng = np.random.default_rng(7)

    if "work_id" not in df: df["work_id"] = [f"WK-{i+1}" for i in range(n)]
    if "created_date" not in df: df["created_date"] = pd.date_range(end=pd.Timestamp.today(), periods=n, freq="D")
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce").fillna(pd.Timestamp.today())

    if "closed_date" in df: df["closed_date"] = pd.to_datetime(df["closed_date"], errors="coerce")
    else: df["closed_date"] = pd.NaT

    if "team" not in df: df["team"] = "General Team"
    df["team"] = df["team"].astype(str).replace({"nan":"General Team", "None":"General Team"})

    if "workstream" not in df: df["workstream"] = "General Work"
    df["workstream"] = df["workstream"].astype(str).replace({"nan":"General Work", "None":"General Work"})

    if "priority" not in df: df["priority"] = "Medium"
    df["priority"] = df["priority"].astype(str).str.title()
    df.loc[~df["priority"].isin(PRIORITIES), "priority"] = "Medium"

    if "status" not in df: df["status"] = "Open"
    df["status"] = df["status"].astype(str).str.title()
    df.loc[~df["status"].isin(STATUSES), "status"] = "Open"

    if "estimated_hours" not in df: df["estimated_hours"] = rng.gamma(2.0, 3.0, size=n)
    df["estimated_hours"] = pd.to_numeric(df["estimated_hours"], errors="coerce").fillna(4.0).clip(lower=0.25)

    if "actual_hours" not in df: df["actual_hours"] = df["estimated_hours"] * rng.normal(1.05, 0.18, size=n)
    df["actual_hours"] = pd.to_numeric(df["actual_hours"], errors="coerce").fillna(df["estimated_hours"]).clip(lower=0.25)

    if "capacity_hours" not in df: df["capacity_hours"] = 320 + rng.normal(0, 25, size=n)
    df["capacity_hours"] = pd.to_numeric(df["capacity_hours"], errors="coerce").fillna(320).clip(lower=40)

    if "due_date" not in df: df["due_date"] = df["created_date"] + pd.to_timedelta(rng.integers(5, 18, size=n), unit="D")
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce").fillna(df["created_date"] + pd.Timedelta(days=10))

    df["is_open"] = df["status"].isin(["Open", "In Progress"]).astype(int)
    df["is_high_priority"] = df["priority"].isin(["High", "Critical"]).astype(int)
    df["age_days"] = (pd.Timestamp.today().normalize() - df["created_date"].dt.normalize()).dt.days.clip(lower=0)
    df["sla_breached"] = ((df["is_open"] == 1) & (pd.Timestamp.today().normalize() > df["due_date"].dt.normalize())).astype(int)
    df["month"] = df["created_date"].dt.to_period("M").astype(str)
    return df

def apply_date_filter(df, mode, custom_range=None):
    out = df.copy()
    max_date = out["created_date"].max()
    if mode == "Last 30 Days": return out[out["created_date"] >= max_date - pd.Timedelta(days=30)]
    if mode == "Last 90 Days": return out[out["created_date"] >= max_date - pd.Timedelta(days=90)]
    if mode == "Last 180 Days": return out[out["created_date"] >= max_date - pd.Timedelta(days=180)]
    if mode == "Custom Date Range" and custom_range:
        start, end = custom_range
        return out[(out["created_date"].dt.date >= start) & (out["created_date"].dt.date <= end)]
    return out

def team_capacity_summary(df):
    if df.empty: return pd.DataFrame()
    g = df.groupby("team").agg(
        work_items=("work_id", "count"),
        open_items=("is_open", "sum"),
        total_estimated_hours=("estimated_hours", "sum"),
        avg_capacity_hours=("capacity_hours", "mean"),
        high_priority_items=("is_high_priority", "sum"),
        sla_breaches=("sla_breached", "sum"),
    ).reset_index()
    g["utilization_pct"] = (g["total_estimated_hours"] / g["avg_capacity_hours"] * 100).replace([np.inf, -np.inf], np.nan).fillna(0).round(1)
    g["pressure_index"] = (
        0.40 * np.minimum(g["utilization_pct"], 160) / 160 * 100 +
        0.25 * (g["open_items"] / g["work_items"].clip(lower=1) * 100) +
        0.20 * (g["high_priority_items"] / g["work_items"].clip(lower=1) * 100) +
        0.15 * (g["sla_breaches"] / g["work_items"].clip(lower=1) * 100)
    ).round(1)
    g["capacity_gap_hours"] = (g["total_estimated_hours"] - g["avg_capacity_hours"]).round(1)
    return g.sort_values("pressure_index", ascending=False)

def monthly_workload(df):
    return df.groupby(pd.Grouper(key="created_date", freq="MS")).agg(
        work_items=("work_id","count"),
        estimated_hours=("estimated_hours","sum"),
        open_items=("is_open","sum")
    ).reset_index()

def simple_forecast(monthly_df, horizon=6):
    if monthly_df.empty: return pd.DataFrame()
    y = monthly_df["work_items"].values.astype(float)
    x = np.arange(len(y))
    if len(y) >= 2:
        coef = np.polyfit(x, y, 1)
        future_x = np.arange(len(y), len(y)+horizon)
        forecast = np.polyval(coef, future_x)
    else:
        forecast = np.repeat(y[-1], horizon)
    last_date = monthly_df["created_date"].max()
    future_dates = pd.date_range(last_date + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    return pd.DataFrame({"created_date": future_dates, "forecast_work_items": np.maximum(0, np.round(forecast, 0)).astype(int)})

def recommendations(summary):
    recs = []
    if summary.empty: return ["No data available for recommendations."]
    high_pressure = summary[summary["pressure_index"] >= 70]
    if not high_pressure.empty:
        recs.append("Prioritize capacity review for high-pressure teams: " + ", ".join(high_pressure["team"].head(3).tolist()) + ".")
    gap = summary[summary["capacity_gap_hours"] > 0]
    if not gap.empty:
        top = gap.sort_values("capacity_gap_hours", ascending=False).iloc[0]
        recs.append(f"{top['team']} shows the largest estimated capacity gap ({top['capacity_gap_hours']:.0f} hours). Consider redistribution or temporary support.")
    sla = summary[summary["sla_breaches"] > 0]
    if not sla.empty:
        top = sla.sort_values("sla_breaches", ascending=False).iloc[0]
        recs.append(f"{top['team']} has the highest SLA breach count. Review aging open items and escalation rules.")
    if not recs:
        recs.append("Workload appears balanced in the selected period. Continue monitoring utilization and demand trends.")
    return recs
