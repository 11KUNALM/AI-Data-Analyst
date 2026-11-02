@'
# AI Data Analyst

An agentic AI-powered web application that automatically analyzes CSV and Excel datasets. Upload a file and it profiles, cleans, and analyzes the data, calculates business KPIs, detects trends and anomalies, forecasts the next period, generates plain-English insights with the Google Gemini API, and exports everything as a PDF report.

## Features

- Automatic dataset profiling (rows, columns, data types, missing values, duplicates)
- Automated data cleaning (deduplication, missing-value imputation, text standardization)
- Descriptive statistics (mean, median, min, max, standard deviation)
- Interactive charts with Plotly
- Automatic dataset type detection (Sales, Employee, Finance, Marketing) with KPIs tailored to each
- Trend analysis with a plain-English explanation
- AI-generated business insights powered by Google Gemini
- Statistical anomaly detection
- Month-over-month forecasting with the assumption stated
- Downloadable PDF report of the full analysis
- Animated 3D interface (Three.js particle background, glassmorphic cards)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Django |
| Data processing | Pandas, NumPy |
| Visualization | Plotly |
| AI | Google Gemini API |
| PDF export | xhtml2pdf |
| Frontend | HTML, CSS, JavaScript, Three.js |

## How It Works

1. The user uploads a CSV or Excel file through the web interface.
2. Pandas loads and profiles the file.
3. The data is cleaned automatically (duplicates removed, missing values filled, text standardized).
4. Descriptive statistics and charts are generated.
5. The dataset type is detected from its column names, and matching business KPIs are calculated.
6. If a date column exists, a trend chart and a forecast are produced.
7. The computed statistics and KPIs are sent to the Gemini API, which writes business insights in plain English.
8. Outliers are flagged with a standard-deviation check.
9. The full analysis can be downloaded as a PDF.

## Build Phases

1. **Foundation**: Django setup, file upload, dataset profiling
2. **Data Engineering**: cleaning, descriptive statistics, first chart
3. **Business Intelligence**: dataset-type detection, KPIs, trend analysis
4. **Agentic AI Layer**: Gemini-generated insights, anomaly detection
5. **Forecasting and Reporting**: forecast, PDF export
6. **Polish**: documentation and demo preparation
7. **Visual Redesign**: 3D glassmorphic interface

## Setup

1. Clone the repository
