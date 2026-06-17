# Capacity & Workload Planning Intelligence

A Streamlit analytics app for workload forecasting, capacity planning, utilization pressure monitoring, resource gap analysis, and scenario-based operational planning.

## What this project does

This project helps answer planning questions such as:

- Which teams or workstreams are likely to face workload pressure?
- How much capacity is available compared with demand?
- Where are utilization risks emerging?
- What happens if demand increases or capacity decreases?
- Which teams require planning attention?

The app supports CSV upload and includes a realistic synthetic data generator so it can run immediately without external data.

## Features

- Planning command center
- Workload explorer
- Capacity forecasting
- Utilization and pressure index
- Resource gap analysis
- Scenario planner
- Planning recommendations
- Data guide and upload support

## Data

You can upload a CSV with columns such as:

- created_date
- team
- workstream
- priority
- status
- estimated_hours
- actual_hours
- capacity_hours
- due_date

If optional columns are missing, the app creates usable defaults.

## Technology Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Scikit-learn

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
## Streamlit implementation

Link: https://capacity-workload-planning-sb.streamlit.app/

## Project Fit

This project fits under Operations Analytics, Capacity Planning, Decision Support, Quality Systems, and Applied Analytics. It demonstrates how analytics can move teams from reactive workload tracking toward proactive planning and resource decision support.

### Additional note

The platform intentionally prioritizes temporal filtering over operational filtering. Capacity planning decisions are typically driven by workload trends across time periods rather than isolated operational segments. Time-based filtering helps maintain a holistic view of organizational demand and resource utilization.
