"""Homework 4: US Traffic Accidents Dashboard, Streamlit + Plotly.

Launch from any working directory with: streamlit run path/to/app.py
The cleaned dataset must be in the same directory as this script.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "US_Accidents_Cleaned.csv"
REPORT_PATH = BASE_DIR / "preparation_report.json"
SEVERITY_COLORS = {"1": "#3788E5", "2": "#2B9A83", "3": "#E4A52A", "4": "#D94F4F"}
REQUIRED_COLUMNS = {
    "ID", "State", "Severity", "Start_Time", "Start_Lat", "Start_Lng",
    "Weather_Group", "Weather_Condition", "Visibility(mi)", "Temperature(F)",
    "Wind_Speed(mph)", "Year", "Month", "Hour",
}

st.set_page_config(
    page_title="US Traffic Accidents Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="Loading prepared accident records…")
def load_data(path: str, last_modified_ns: int) -> pd.DataFrame:
    """Cache CSV loading; mtime invalidates the cache when preparation reruns."""
    del last_modified_ns
    data = pd.read_csv(path, parse_dates=["Start_Time"], low_memory=False)
    missing = sorted(REQUIRED_COLUMNS.difference(data.columns))
    if missing:
        raise ValueError(f"Cleaned CSV is missing required columns: {', '.join(missing)}")
    data["State"] = data["State"].astype("string")
    data["Weather_Group"] = data["Weather_Group"].fillna("Unknown")
    return data


def get_weather_chart_data(data: pd.DataFrame, variable: str) -> tuple[pd.DataFrame, int, str]:
    """Return categories, report counts and missing observations for one weather variable."""
    if variable == "Weather group":
        labels = data["Weather_Group"].fillna("Unknown").astype(str)
        caption = "Groups are estimated from the dataset's weather descriptions."
        count_missing = int(labels.eq("Unknown").sum())
    else:
        settings = {
            "Visibility (mi)": (
                "Visibility(mi)", [-0.001, 1, 3, 5, 10, np.inf],
                ["<1", "1–<3", "3–<5", "5–<10", "10+"],
                "Visibility in miles (non-missing observations only)",
            ),
            "Temperature (°F)": (
                "Temperature(F)", [-np.inf, 32, 50, 68, 86, np.inf],
                ["<32", "32–<50", "50–<68", "68–<86", "86+"],
                "Temperature in °F (non-missing observations only)",
            ),
            "Wind speed (mph)": (
                "Wind_Speed(mph)", [-0.001, 5, 15, 25, 40, np.inf],
                ["<5", "5–<15", "15–<25", "25–<40", "40+"],
                "Wind speed in mph (non-missing observations only)",
            ),
        }
        column, edges, bins, caption = settings[variable]
        raw = pd.to_numeric(data[column], errors="coerce")
        count_missing = int(raw.isna().sum())
        labels = pd.cut(raw, bins=edges, labels=bins, right=False)
    counts = labels.value_counts(sort=False, dropna=True)
    if variable == "Weather group":
        counts = counts.sort_values(ascending=False)
    result = counts.rename_axis("Condition").reset_index(name="Count")
    result["Condition"] = result["Condition"].astype(str)
    return result, count_missing, caption


st.title("🚗 US Traffic Accidents Dashboard")
st.write(
    "Explore **reported U.S. traffic accidents** by state, traffic-impact severity, "
    "weather conditions, and time in a reproducible sample of the 2016–2023 "
    "[US-Accidents dataset](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents/)."
)
st.caption(
    "These visualizations show accident **reports in the cleaned sample**, not "
    "the probability or risk of a crash. Traffic exposure, reporting coverage, and "
    "time-period completeness differ across places and years."
)

if not DATA_PATH.is_file():
    st.error("Missing data file: **US_Accidents_Cleaned.csv**")
    st.write(
        "The dashboard needs a prepared dataset beside `app.py`. "
        "Run the preparation script **on your computer** before starting the app."
    )
    st.code(
        'python prepare_data.py "C:/path/to/US_Accidents_March23.csv"\n'
        '# Or, after installing kagglehub:\n'
        'python prepare_data.py --download-kaggle\n'
        'python -m streamlit run app.py',
        language="bash",
    )
    st.caption(f"Expected prepared CSV location: {DATA_PATH}")
    st.info(
        "For Streamlit Community Cloud, commit or upload the **prepared CSV** "
        "with app.py and requirements.txt. The full raw Kaggle dataset is not "
        "downloaded by the deployed app."
    )
    st.stop()

try:
    df = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime_ns)
except (ValueError, OSError) as exc:
    st.error(f"Could not read the cleaned data: {exc}")
    st.info("Regenerate the data with prepare_data.py and retry.")
    st.stop()

if df.empty:
    st.warning("The prepared dataset has no valid rows. Re-run prepare_data.py.")
    st.stop()

with st.sidebar:
    st.header("Explore the data")
    state_choices = sorted(df["State"].dropna().unique().tolist())
    states = st.multiselect(
        "States", state_choices,
        placeholder="All states",
        help="Leave the selection empty to include all available states.",
    )
    st.caption("All states" if not states else f"{len(states)} selected state(s)")
    year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
    if year_min == year_max:
        years = (year_min, year_max)
        st.write(f"**Year:** {year_min}")
    else:
        years = st.slider("Year range", year_min, year_max, (year_min, year_max))
    severities = st.multiselect(
        "Severity levels (1 = least; 4 = most traffic impact)",
        [1, 2, 3, 4], default=[1, 2, 3, 4],
    )
    weather_choices = ["All weather groups"] + sorted(
        df["Weather_Group"].dropna().unique().tolist()
    )
    selected_weather = st.selectbox("Weather group filter", weather_choices)
    map_cap = st.slider("Maximum map points", 500, 5_000, 3_000, 500)
    st.caption("All filters affect all charts. Map points are additionally sampled for speed.")

if not severities:
    st.warning("Select at least one severity level in the sidebar.")
    st.stop()

mask = df["Year"].between(*years) & df["Severity"].isin(severities)
if states:
    mask &= df["State"].isin(states)
if selected_weather != "All weather groups":
    mask &= df["Weather_Group"].eq(selected_weather)
filtered = df.loc[mask].copy()

if filtered.empty:
    st.warning("No accident reports match these filters. Change the selections in the sidebar.")
    st.stop()

n = len(filtered)
peak_level = int(filtered["Severity"].value_counts().idxmax())
level_four = int(filtered["Severity"].eq(4).sum())
state_count = int(filtered["State"].nunique())
monthly = (
    filtered.groupby(filtered["Start_Time"].dt.to_period("M"))
    .size().sort_index().rename("Count")
)
peak_month = monthly.idxmax()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Reports in filtered sample", f"{n:,}")
k2.metric("States represented", f"{state_count:,}")
k3.metric("Severity 4 reports", f"{level_four / n:.1%}")
k4.metric("Most common severity", str(peak_level))

st.subheader("Key insights · current filter selection")
known_weather = filtered.loc[filtered["Weather_Group"].ne("Unknown"), "Weather_Group"]
weather_insight = (
    f"The most frequently recorded known weather group is "
    f"**{known_weather.value_counts().idxmax()}** "
    f"({known_weather.value_counts().max():,} reports)."
    if not known_weather.empty
    else "No records with a known weather group are present in this selection."
)
insights = [
    f"**Severity {peak_level}** is the most common traffic-impact level "
    f"({filtered['Severity'].eq(peak_level).mean():.1%} of selected reports).",
    weather_insight,
    f"**{peak_month.strftime('%B %Y')}** has the most sampled reports "
    f"among the selected months ({monthly.max():,}).",
]
for insight in insights:
    st.markdown(f"- {insight}")
st.caption("Patterns describe recorded reports, not causes or exposure-adjusted risk.")

map_tab, weather_tab, time_tab, methods_tab = st.tabs(
    ["🗺️ Map & severity", "🌦️ Weather", "📈 Time trend", "📋 Data preparation"]
)

with map_tab:
    map_col, severity_col = st.columns([1.5, 1], gap="large")
    with map_col:
        st.subheader("1 · Interactive accident location map")
        locations = filtered.sample(n=min(n, map_cap), random_state=42).copy()
        locations["Severity_Label"] = locations["Severity"].astype(str)
        fig_map = px.scatter_map(
            locations,
            lat="Start_Lat", lon="Start_Lng", color="Severity_Label",
            category_orders={"Severity_Label": ["1", "2", "3", "4"]},
            color_discrete_map=SEVERITY_COLORS,
            hover_name="State",
            hover_data={
                "Severity_Label": True, "Start_Time": True,
                "Weather_Group": True, "Start_Lat": False, "Start_Lng": False,
            },
            map_style="open-street-map", zoom=2.7, center={"lat": 39, "lon": -97},
            labels={"Severity_Label": "Traffic-impact severity"},
        )
        fig_map.update_traces(marker={"size": 7, "opacity": 0.70})
        fig_map.update_layout(height=480, margin=dict(l=0, r=0, t=0, b=0), legend_title_text="Severity")
        st.plotly_chart(fig_map, use_container_width=True)
        st.caption(
            f"Plotly map displays {len(locations):,} reproducibly sampled locations "
            f"out of {n:,} filtered records. Sampling only limits map markers, "
            "not any other chart. Overlapping markers may conceal reports."
        )

    with severity_col:
        st.subheader("2 · Accident severity distribution")
        severity_counts = (
            filtered["Severity"].value_counts()
            .reindex([1, 2, 3, 4], fill_value=0)
            .rename_axis("Severity").reset_index(name="Count")
        )
        severity_counts["Severity"] = severity_counts["Severity"].astype(str)
        severity_counts["Percent"] = severity_counts["Count"] / n * 100
        fig_severity = px.bar(
            severity_counts, x="Severity", y="Count", color="Severity",
            category_orders={"Severity": ["1", "2", "3", "4"]},
            color_discrete_map=SEVERITY_COLORS,
            text="Count", custom_data=["Percent"],
            labels={"Severity": "Traffic-impact severity (1–4)", "Count": "Sampled reports"},
        )
        fig_severity.update_traces(
            hovertemplate="Severity %{x}<br>%{y:,} reports<br>"
            "%{customdata[0]:.1f}% of filtered sample<extra></extra>",
            textposition="outside",
        )
        fig_severity.update_layout(
            height=480, showlegend=False, margin=dict(t=25, b=30, l=0, r=8),
        )
        st.plotly_chart(fig_severity, use_container_width=True)
        st.caption(
            "Severity 1–4 describes estimated impact on **traffic**, not the extent "
            "of injuries or fatalities."
        )

with weather_tab:
    st.subheader("3 · Weather and traffic conditions")
    st.write(
        "Compare the count of accident reports across recorded weather categories or "
        "binned visibility, temperature, and wind speed."
    )
    weather_variable = st.radio(
        "Weather measure", ["Weather group", "Visibility (mi)",
                            "Temperature (°F)", "Wind speed (mph)"],
        horizontal=True,
    )
    weather_counts, missing_in_measure, weather_detail = get_weather_chart_data(
        filtered, weather_variable
    )
    if weather_counts.empty or int(weather_counts["Count"].sum()) == 0:
        st.info("No valid observations are available for this measure and filter combination.")
    else:
        fig_weather = px.bar(
            weather_counts, x="Condition", y="Count", text="Count",
            labels={"Condition": weather_variable, "Count": "Sampled accident reports"},
            title=f"Reports by {weather_variable.lower()}",
        )
        fig_weather.update_traces(hovertemplate="%{x}<br>%{y:,} reports<extra></extra>")
        fig_weather.update_layout(height=450, xaxis_title=weather_variable)
        fig_weather.update_xaxes(categoryorder="array", categoryarray=weather_counts["Condition"].tolist())
        st.plotly_chart(fig_weather, use_container_width=True)
    st.caption(
        f"{weather_detail} {missing_in_measure:,} of {n:,} filtered reports "
        "have missing or unknown values for this measure. The 'Unknown' weather "
        "group is displayed explicitly; missing numeric measurements are omitted "
        "from the corresponding chart."
    )
    st.info(
        "Interpret these as **associations among accident reports**. More reports "
        "during a particular weather condition do **not** establish that it causes "
        "more crashes: weather exposure, traffic volume, and reporting vary."
    )

with time_tab:
    st.subheader("4 · Monthly accident-report trend")
    trend = monthly.rename_axis("Period").reset_index()
    trend["MonthStart"] = trend["Period"].dt.to_timestamp()
    fig_time = px.line(
        trend, x="MonthStart", y="Count", markers=True,
        labels={"MonthStart": "Calendar month", "Count": "Sampled accident reports"},
        title="Reported accidents per observed month in the filtered sample",
    )
    fig_time.update_layout(height=470)
    st.plotly_chart(fig_time, use_container_width=True)
    st.caption(
        "Only months with observations are plotted; absent months may reflect "
        "missing coverage rather than zero accidents. The source begins in "
        "February 2016 and ends in March 2023, leaving partial years. Changes in "
        "reporting coverage may influence the apparent trend."
    )
    st.subheader("Additional view · Reports by start hour")
    hourly = (
        filtered.groupby("Hour").size().reindex(range(24), fill_value=0)
        .rename_axis("Hour").reset_index(name="Count")
    )
    fig_hour = px.bar(
        hourly, x="Hour", y="Count",
        labels={"Hour": "Local start hour (0–23)", "Count": "Sampled reports"},
    )
    fig_hour.update_layout(height=330)
    fig_hour.update_xaxes(dtick=1)
    st.plotly_chart(fig_hour, use_container_width=True)
    st.caption("Hour represents the record's local wall-clock time; no US time-zone conversion was applied.")

with methods_tab:
    st.subheader("Data cleaning, sampling and limitations")
    if REPORT_PATH.is_file():
        try:
            report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            st.warning(f"Cannot read preparation_report.json: {exc}")
            report = None
    else:
        report = None

    if report is None:
        st.warning(
            "preparation_report.json is not available. Run prepare_data.py "
            "and include the report with your deployed dataset for audited counts."
        )
    else:
        st.markdown(
            f"**Sampling:** {report.get('sampling_fraction', 0.02):.1%} independent "
            "row selection across the full CSV, fixed random seed 42. "
            "The source is read in 250,000-row chunks."
        )
        a, b, c = st.columns(3)
        a.metric("Source records scanned", f"{report['source_rows_inspected']:,}")
        b.metric("Random sample before cleaning", f"{report['sampled_rows_before_cleaning']:,}")
        c.metric("Sample records excluded", f"{report['total_sampled_rows_excluded']:,}")
        st.markdown("**Excluded rows from sampled records (sequential counts)**")
        exclusion = pd.DataFrame(
            report["sample_exclusions_applied_sequentially"].items(),
            columns=["Exclusion reason", "Rows excluded"],
        )
        st.dataframe(exclusion, hide_index=True, use_container_width=True)
        st.markdown("**Missing values in full source (selected fields only)**")
        source_missing = pd.DataFrame(
            report["source_missing_counts_selected_columns"].items(),
            columns=["Field", "Missing count"],
        )
        source_missing["Missing %"] = (
            source_missing["Missing count"] / report["source_rows_inspected"] * 100
        ).round(2)
        st.dataframe(source_missing, hide_index=True, use_container_width=True)
        with st.expander("Full preparation report"):
            st.json(report)

    st.markdown("**Missing values in cleaned sample**")
    cleaned_missing = pd.DataFrame({
        "Field": df.columns,
        "Missing count": df.isna().sum().values,
        "Missing %": (df.isna().mean() * 100).round(2).values,
    })
    st.dataframe(cleaned_missing, hide_index=True, use_container_width=True)
    st.markdown("**Filtered record preview (first 50 rows)**")
    st.dataframe(filtered.head(50), hide_index=True, use_container_width=True)
    st.write(
        "**Missing-value policy:** Missing core identifiers, state, date/time, severity, "
        "or coordinates cause exclusion from the sampled data. Missing weather "
        "descriptions are shown as Unknown; missing numeric weather values stay "
        "missing, and negative visibility/wind speed are set to missing."
    )
    st.write(
        "**Interpretation limitations:** This is a descriptive sample of reported "
        "accidents, not an exposure-adjusted crash-rate dataset. State, weather, and "
        "time differences may reflect reporting practices, traffic exposure, or "
        "incomplete time coverage rather than differences in accident risk."
    )
    st.markdown(
        "**Dataset citation:** [US-Accidents: A Countrywide Traffic Accident Dataset "
        "(Kaggle)](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents/)"
    )
