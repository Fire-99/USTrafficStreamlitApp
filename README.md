# US Traffic Accidents Dashboard 

An interactive traffic accident exploration dashboard developed using **Python, Pandas, Streamlit, and Plotly**. It uses a reproducible sample of the [US-Accidents: A Countrywide Traffic Accident Dataset](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents/) to explore patterns in **reported accidents** by state, estimated traffic-impact severity, weather conditions, and time.

**Dataset coverage:** Approximately February 2016–March 2023, with over 7.7 million source accident reports. **Important:** Accident-report counts are not crash-risk rates; they are affected by traffic exposure, geographic reporting coverage, and incomplete periods.

## 1.Requirements covered

| Requirement | Implementation |
| --- | --- |
| Data preparation | Pandas-based CSV processing, missing-value checks, cleaning, and documentation |
| State-based filtering | Select one or more states; an empty selection includes all states |
| Severity filtering | Select any combination of Severity 1, 2, 3, and 4 |
| Time filtering | Interactive year-range slider |
| Accident location map | Plotly interactive map using latitude and longitude, colored by severity |
| Severity distribution | Plotly bar chart showing report counts for severity levels 1–4 |
| Weather and traffic conditions | Plotly bar charts for weather groups or binned visibility, temperature, and wind speed |
| Time trend | Monthly Plotly line chart, plus an optional hourly bar chart |
| Insights | Filter-responsive KPIs and short, data-supported observations |
| Empty selections | Graceful messages when filters return no records |

The application has **four tabs**: **Map & severity**, **Weather**, **Time trend**, and **Data preparation**. The map and severity chart share the first tab. The dashboard uses a dark visual presentation with distinct colors for the four severity levels; it does not require a separate `.streamlit/config.toml` to run.

### A. New York and Virginia (NY + VA)

**Filters shown:** NY and VA; 2016–2023; Severities 1–4; all weather groups. The map-point limit only changes how many markers are drawn, not the counts in the other charts.

**Reports in the filtered sample:** **12,912** across **2 selected states**.

| Traffic-impact severity | Sampled reports | Share of selected reports |
| --- | ---: | ---: |
| 1 (least traffic impact) | 86 | 0.7% |
| 2 | 9,812 | 76.0% |
| 3 | 2,431 | 18.8% |
| 4 (greatest traffic impact) | 583 | 4.5% |
| **Total** | **12,912** | **100%** |

**Finding:** Severity **2** is the most frequently recorded level, with **9,812 reports (76.0%)**. Severity **4** accounts for **583 reports (4.5%)**. These levels refer to estimated **traffic disruption**, not injury severity or fatalities.

| Weather group | Sampled reports |
| --- | ---: |
| Cloudy | 5,869 |
| Clear / Fair | 4,675 |
| Rain | 1,175 |
| Snow / Ice | 501 |
| Unknown | 385 |
| Fog / Mist / Haze | 188 |
| Thunderstorm | 112 |
| Other | 7 |

**Finding:** **Cloudy** is the most frequently recorded **known** weather group (**5,869 reports**). The distribution does **not** establish that cloudy weather causes more accidents. `Unknown` observations remain in the weather-group chart.

**Monthly trend:** The NY + VA screenshot shows a peak in 2022, but the exact peak-month count is **not legible** in the available screenshot. Verify it using the app's hover tooltip or the calculation in Section 7 before citing a number for this filter combination.

### B. New York, Arkansas, and Colorado (NY + AR + CO)

A different dashboard screenshot used **NY, AR, and CO** with 2016–2023, all severity levels, and all weather groups. It showed:

- **9,326** reports across **3 states**.
- **Severity 2:** most frequent, at **73.6%** of selected reports.
- **Severity 4:** **4.6%** of selected reports.
- **Cloudy:** most frequently recorded known weather group, with **4,584** reports.
- **September 2022:** highest observed month, with **311** sampled reports.

**Do not combine** the September 2022 count of **311** from the NY + AR + CO view with the **12,912-report** NY + VA view. They are different filter selections.

## 2. Data preparation methodology

The script `prepare_data.py`:

1. Reads `US_Accidents_March23.csv` in **250,000-row chunks** to limit memory use.
2. Scans the original source for missing values in relevant fields (`ID`, `State`, `Severity`, `Start_Time`, `Start_Lat`, `Start_Lng`, `Weather_Condition`, `Visibility(mi)`, `Temperature(F)`, and `Wind_Speed(mph)`).
3. Selects an approximately **2% independent random sample** with a fixed NumPy seed of **42**; the exact number sampled can vary slightly because each row is selected independently.
4. Excludes sampled records with blank IDs/states, invalid dates, severity outside 1–4, missing/invalid coordinates, or duplicate IDs **within the sample**. Exclusion counts are recorded sequentially.
5. Replaces missing weather descriptions with `Unknown`, classifies descriptions into weather groups, retains missing numeric weather measurements, and changes negative visibility/wind-speed readings to missing.
6. Converts `Start_Time` to datetime and derives `Year`, `Month`, `Hour`, and `Day_of_Week` using the source's local wall-clock timestamps without timezone conversion.
7. Creates the cleaned data file, a state-year summary, and a JSON preparation report. The original Kaggle CSV is not modified.

**Generated outputs:**

- `US_Accidents_Cleaned.csv` — the cleaned sample used by the dashboard.
- `Accidents_By_State_Year.csv` — optional state/year aggregated counts.
- `preparation_report.json` — source and sample counts, missing values, sequential exclusions, sampling settings, and limitations.

**Data-preparation counts:** The exact full-dataset rows scanned, sampled rows removed, and final cleaned-sample size must come from your own `preparation_report.json`. The **12,912** and **9,326** figures above are *filtered dashboard results*, not source-row or full-cleaned-sample totals.

## 3. Installation and running locally

Install Python 3.10+ and run these commands in the project directory:

```bash
python -m pip install -r requirements.txt
```

Download the original Kaggle CSV and run:

```bash
python prepare_data.py "C:/full/path/to/US_Accidents_March23.csv"
```

Or, to download through Kagglehub, install it and use the preparation script's built-in option:

```bash
python -m pip install kagglehub
python prepare_data.py --download-kaggle
```

Kagglehub is needed only for downloading the **original** CSV; it is **not** needed when the hosted app reads the prepared CSV.

Then start Streamlit:

```bash
python -m streamlit run app.py
```

If using Jupyter Notebook for installation, use `%pip install -r requirements.txt` and then run the commands in a terminal. `prepare_data.py` writes its outputs into its own folder by default, alongside `app.py`, avoiding the earlier **data file not found** error.

## 4. Files to upload to GitHub

Repository: [Fire-99/USTrafficStreamlitApp](https://github.com/Fire-99/USTrafficStreamlitApp)

```text
USTrafficStreamlitApp/
├── app.py                       # Main dashboard
├── prepare_data.py              # Reproducible data preparation
├── report_results.py            # Optional overall results helper
├── requirements.txt             # Packages for deployment
├── README.md                    # Project instructions and findings
├── US_Accidents_Cleaned.csv     # REQUIRED: prepared dataset
├── preparation_report.json      # REQUIRED for documented methods tab
└── Accidents_By_State_Year.csv  # Optional aggregate output
```

```bash
python prepare_data.py "C:/full/path/to/US_Accidents_March23.csv" --fraction 0.01
```

This creates an approximately 1% sample. **If you change the sampling fraction, regenerate the results and report screenshots**; the 2%-sample figures listed above may no longer apply. For very large files, use an appropriate supported hosting method rather than committing the raw Kaggle CSV.


## 5. How to verify results from the actual CSV

To generate **overall, all-state** results for the entire cleaned sample (not the NY + VA subset), run:

```bash
python report_results.py
```

To obtain an **exact peak month for the NY + VA filtered view**, run this Python code in the folder containing the cleaned CSV:

```python
import pandas as pd

accidents = pd.read_csv("US_Accidents_Cleaned.csv", parse_dates=["Start_Time"])
selected = accidents[
    accidents["State"].isin(["NY", "VA"])
    & accidents["Year"].between(2016, 2023)
    & accidents["Severity"].isin([1, 2, 3, 4])
]
monthly_counts = selected.groupby(selected["Start_Time"].dt.to_period("M")).size()
print("Total reports:", len(selected))
print("Peak month:", monthly_counts.idxmax())
print("Peak month reports:", int(monthly_counts.max()))
```

If your output differs from the screenshots, confirm that you are using the **same cleaned dataset** and filters. Do not transfer numerical findings between filter configurations.

## 6. Limitations and references

- **Severity 1–4 estimates impact on traffic**, not the number or seriousness of injuries or fatalities.
- Counts describe **reported accidents in the chosen sample**, not crash probability or risk. Higher recorded counts may reflect traffic exposure, availability of reports, or changes in coverage.
- Weather patterns are **descriptive associations**, not evidence that weather conditions cause crashes.
- The dataset contains incomplete **2016** and **2023** coverage; monthly and state comparisons require caution.
- Map display limits affect only plotted markers and do **not** reduce the records used for other charts.

**References:** [US-Accidents (Kaggle)](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents/) · [Streamlit documentation](https://docs.streamlit.io/) · [Plotly Python](https://plotly.com/python/) · [Pandas documentation](https://pandas.pydata.org/docs/) · [NumPy documentation](https://numpy.org/doc/)
