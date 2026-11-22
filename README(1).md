# Homework 4 — US Traffic Accidents Dashboard

**Source:** [US-Accidents on Kaggle](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents/). Uses the reported-accidents dataset (approximately February 2016–March 2023). Built with **Streamlit** and **Plotly**.

## Dashboard visual theme

This version uses a **Midnight Ocean** palette: navy gradient page background,
soft navy chart panels, teal headings and interactive accents, and coordinated
blue / teal / amber / coral severity colors. KPI metrics and insight cards have
subtle borders and elevated panels; the Plotly map uses a matching dark basemap.
The sidebar uses the same palette.

The theme is configured in **`.streamlit/config.toml`** and enhanced with CSS inside
`app.py`. Keep that folder when publishing the application so native Streamlit
widgets also appear in the intended dark theme. The chart colors remain
accessible as separate colors rather than relying only on a continuous scale.

## 1. Install dependencies

Run in the folder containing `app.py` and `prepare_data.py`:

```bash
python -m pip install -r requirements.txt
```

To run this from Jupyter Notebook instead, use `%pip install -r requirements.txt` in a cell.

## 2. Prepare the data (required once)

Download and unzip `US_Accidents_March23.csv` from Kaggle. Kagglehub users can find the file path by running:

```python
import kagglehub
from pathlib import Path
csv_path = Path(kagglehub.dataset_download('sobhanmoosavi/us-accidents')) / 'US_Accidents_March23.csv'
print(csv_path)
```

Kagglehub is optional and used only to **download** the source CSV; it is not a dependency of the deployed app.

In the terminal, run (substitute your actual CSV path):

```bash
python prepare_data.py "C:/full/path/to/US_Accidents_March23.csv"
```

Alternatively, in Jupyter Notebook, with the project folder as your working directory:

```python
import subprocess, sys
subprocess.run([sys.executable, 'prepare_data.py', str(csv_path)], check=True)
```

**Fix for the previous "Data file not found" error:** `prepare_data.py` now **always writes its outputs alongside `app.py` by default**, not wherever the terminal happened to be opened.

The script creates these three files beside `app.py`:

- `US_Accidents_Cleaned.csv` — reproducible approximately 2% random sample
- `Accidents_By_State_Year.csv` — aggregated sample counts (optional for extra reporting)
- `preparation_report.json` — source missing values, exclusions, sample size and caveats

The method streams the full original source CSV in chunks of 250,000 rows, records missing values in all original rows for selected columns, and randomly samples each row with probability 2% (seed 42). It cleans sampled records, drops duplicate IDs **within the sample**, replaces missing weather descriptions with `Unknown`, and retains missing numerical weather readings as missing. Dates are parsed and Year/Month/Hour/Day_of_Week are derived. The original source is not modified.

If your cleaned CSV becomes too large to upload to GitHub, rerun with `--fraction 0.01` for an approximate 1% sample (document the updated value). The dashboard reads the true fraction from the preparation report.

## 3. Start the app locally

```bash
python -m streamlit run app.py
```

You should see **four interactive Plotly visualizations** in tabs: (1) sampled location map (Plotly `scatter_map`), (2) severity distribution, (3) weather conditions (with optional binned visibility / temperature / wind speed), and (4) monthly trend. An optional hourly plot is included. All required visuals respond to state, severity, year-range, and weather sidebar filters. The map may downsample **filtered** points independently for display speed. Empty results show a message rather than an exception.

## 4. Deploy and submit

Upload these **required runtime files together** to your GitHub repository:

```text
app.py
requirements.txt
US_Accidents_Cleaned.csv
preparation_report.json
```

Also include `prepare_data.py`, `README.md`, **`.streamlit/config.toml`**, and (optional) `Accidents_By_State_Year.csv` for reproducibility. **Do not upload the original several-GB CSV**. Do not omit the cleaned CSV: Streamlit Community Cloud cannot read a local file that exists only on your computer.

1. Create or open a GitHub repo containing the files above.
2. Sign in to https://share.streamlit.io and create a new app from the repository. Select `app.py` as the entrypoint.
3. Wait until the deployment finishes and verify that all tabs load, filters work, and there is no missing-file error.
4. Test the **public** app URL in a private/incognito browser.
5. Submit the code, the working public Streamlit link, and a report containing **screenshots from the actual running dashboard** (not just the link).

**Public Streamlit app URL:** _Insert your deployed URL here after deployment._

## 5. Suggested report structure (according to Homework 4)

1. **Introduction:** Dataset, purpose, intended audience.
2. **Data Exploration and Preparation:** Original record count and missingness from `preparation_report.json`, 2% sample, exclusion counts, date features and limitations.
3. **Dashboard Design:** Sidebar + five tabs; insert a **screenshot of the main dashboard**.
4. **Key Features and Visualizations:** State/severity/year/weather filters, map, severity, weather, monthly trend; insert screenshots of required visualizations.
5. **Insights and Findings:** Use numeric values actually shown in your running dashboard (e.g., leading severity class, peak month, most frequent recorded weather group). Do not invent results.
6. **Future Improvements:** Add vehicle-miles-traveled/traffic denominators, consistency checks, more rigorous coverage validation, and performance improvements.
7. **Conclusion:** What the interactive dashboard reveals, with descriptive caveats.
8. **References:** Kaggle data source, Plotly and Streamlit docs.

## Important interpretation note

Severity 1–4 describes **impact on traffic**, not injury severity. Sampled report counts are **not risk estimates**. Periods in the original data are incomplete and reporting may vary by location/time. Associations with weather do not establish causal effects without exposure data.
