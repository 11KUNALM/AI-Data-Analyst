import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from google import genai
from django.conf import settings
from xhtml2pdf import pisa
from io import BytesIO


def load_dataset(file_path):
    """Reads a CSV or Excel file into a pandas DataFrame."""
    lower_path = file_path.lower()

    if lower_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif lower_path.endswith('.xlsx') or lower_path.endswith('.xlsm'):
        df = pd.read_excel(file_path, engine='openpyxl')
    elif lower_path.endswith('.xls'):
        df = pd.read_excel(file_path, engine='xlrd')
    else:
        raise ValueError(
            f"Unsupported file type: '{file_path}'. Please upload a .csv, .xlsx, or .xls file."
        )

    return df


def profile_dataset(df):
    """Looks at the DataFrame and returns a summary dictionary."""

    summary = {}

    summary['total_rows'] = len(df)
    summary['total_columns'] = len(df.columns)

    summary['column_types'] = {
        col: str(dtype) for col, dtype in df.dtypes.items()
    }

    missing = df.isnull().sum()
    summary['missing_values'] = {
        col: int(count) for col, count in missing.items() if count > 0
    }

    summary['duplicate_rows'] = int(df.duplicated().sum())

    summary['blank_rows'] = int(df.isnull().all(axis=1).sum())

    summary['preview'] = df.head(5).to_dict(orient='records')
    summary['columns'] = list(df.columns)

    return summary


def clean_dataset(df):
    """Cleans the dataset and returns (cleaned_df, cleaning_report)."""

    report = {}
    original_rows = len(df)

    duplicates_removed = int(df.duplicated().sum())
    df = df.drop_duplicates()
    report['duplicates_removed'] = duplicates_removed

    text_columns = df.select_dtypes(include='object').columns
    for col in text_columns:
        df[col] = df[col].astype(str).str.strip()

    for col in text_columns:
        df[col] = df[col].str.title()

    missing_filled = {}
    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        if missing_count > 0:
            if df[col].dtype in ['int64', 'float64']:
                fill_value = df[col].median()
                df[col] = df[col].fillna(fill_value)
                missing_filled[col] = f"filled {missing_count} with median ({fill_value})"
            else:
                df[col] = df[col].fillna('Unknown')
                missing_filled[col] = f"filled {missing_count} with 'Unknown'"

    report['missing_filled'] = missing_filled
    report['rows_before'] = original_rows
    report['rows_after'] = len(df)

    return df, report


def descriptive_statistics(df):
    """Returns mean, median, min, max, std dev, etc. for every numeric column."""

    numeric_df = df.select_dtypes(include=['int64', 'float64'])
    stats = {}

    for col in numeric_df.columns:
        stats[col] = {
            'mean': round(numeric_df[col].mean(), 2),
            'median': round(numeric_df[col].median(), 2),
            'min': round(numeric_df[col].min(), 2),
            'max': round(numeric_df[col].max(), 2),
            'std_dev': round(numeric_df[col].std(), 2),
        }

    return stats


def build_bar_chart(df):
    """Builds a bar chart of the first numeric column grouped by the first text column, if possible."""

    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    text_cols = df.select_dtypes(include='object').columns

    if len(numeric_cols) == 0 or len(text_cols) == 0:
        return None

    x_col = text_cols[0]
    y_col = numeric_cols[0]

    grouped = df.groupby(x_col)[y_col].sum().reset_index()

    fig = px.bar(
        grouped,
        x=x_col,
        y=y_col,
        title=f"{y_col} by {x_col}",
        labels={x_col: x_col, y_col: y_col},
    )

    chart_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
    return chart_html


def detect_dataset_type(df):
    """Guesses what kind of business dataset this is, based on column names."""

    columns_lower = [col.lower() for col in df.columns]

    sales_keywords = ['sales', 'revenue', 'order', 'product', 'quantity', 'price']
    employee_keywords = ['employee', 'salary', 'department', 'attrition', 'designation']
    finance_keywords = ['income', 'expense', 'profit', 'budget', 'transaction']
    marketing_keywords = ['click', 'impression', 'conversion', 'campaign', 'ctr', 'cpc']

    def score(keywords):
        return sum(1 for kw in keywords if any(kw in col for col in columns_lower))

    scores = {
        'sales': score(sales_keywords),
        'employee': score(employee_keywords),
        'finance': score(finance_keywords),
        'marketing': score(marketing_keywords),
    }

    best_match = max(scores, key=scores.get)

    if scores[best_match] == 0:
        return 'generic'

    return best_match


def calculate_kpis(df, dataset_type):
    """Calculates relevant business KPIs based on the detected dataset type."""

    kpis = {}
    columns_lower = {col.lower(): col for col in df.columns}

    def find_column(possible_names):
        for name in possible_names:
            for col_lower, col_actual in columns_lower.items():
                if name in col_lower:
                    return col_actual
        return None

    if dataset_type == 'sales':
        sales_col = find_column(['sales', 'revenue', 'amount'])
        qty_col = find_column(['quantity', 'qty'])
        product_col = find_column(['product'])

        if sales_col:
            kpis['Total Sales'] = round(df[sales_col].sum(), 2)
            kpis['Average Order Value'] = round(df[sales_col].mean(), 2)
        if qty_col:
            kpis['Total Quantity Sold'] = int(df[qty_col].sum())
        kpis['Total Orders'] = len(df)
        if product_col and sales_col:
            top_product = df.groupby(product_col)[sales_col].sum().idxmax()
            kpis['Top Product'] = top_product

    elif dataset_type == 'employee':
        salary_col = find_column(['salary'])
        dept_col = find_column(['department'])

        kpis['Total Employees'] = len(df)
        if salary_col:
            kpis['Average Salary'] = round(df[salary_col].mean(), 2)
            kpis['Highest Salary'] = round(df[salary_col].max(), 2)
            kpis['Lowest Salary'] = round(df[salary_col].min(), 2)
        if dept_col:
            kpis['Department Count'] = df[dept_col].nunique()

    elif dataset_type == 'finance':
        income_col = find_column(['income', 'revenue'])
        expense_col = find_column(['expense', 'cost'])

        if income_col:
            kpis['Total Income'] = round(df[income_col].sum(), 2)
        if expense_col:
            kpis['Total Expenses'] = round(df[expense_col].sum(), 2)
        if income_col and expense_col:
            kpis['Net Profit'] = round(df[income_col].sum() - df[expense_col].sum(), 2)

    elif dataset_type == 'marketing':
        clicks_col = find_column(['click'])
        impressions_col = find_column(['impression'])
        conversions_col = find_column(['conversion'])

        if clicks_col and impressions_col:
            ctr = (df[clicks_col].sum() / df[impressions_col].sum()) * 100
            kpis['CTR (%)'] = round(ctr, 2)
        if conversions_col and clicks_col:
            conv_rate = (df[conversions_col].sum() / df[clicks_col].sum()) * 100
            kpis['Conversion Rate (%)'] = round(conv_rate, 2)

    else:
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        kpis['Total Records'] = len(df)
        kpis['Numeric Columns'] = len(numeric_cols)
        if len(numeric_cols) > 0:
            kpis[f'Sum of {numeric_cols[0]}'] = round(df[numeric_cols[0]].sum(), 2)

    return kpis


def detect_trend(df):
    """If there's a date column and a numeric column, builds a trend line chart."""

    date_col = None
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            date_col = col
            break

    if date_col is None:
        return None, None

    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    except Exception:
        return None, None

    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) == 0:
        return None, None

    value_col = numeric_cols[0]

    trend_df = df.dropna(subset=[date_col]).sort_values(date_col)
    trend_df = trend_df.groupby(trend_df[date_col].dt.to_period('M'))[value_col].sum().reset_index()
    trend_df[date_col] = trend_df[date_col].astype(str)

    if len(trend_df) < 2:
        return None, None

    first_value = trend_df[value_col].iloc[0]
    last_value = trend_df[value_col].iloc[-1]
    direction = "increasing" if last_value > first_value else "decreasing"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_df[date_col], y=trend_df[value_col], mode='lines+markers'))
    fig.update_layout(title=f"{value_col} Trend Over Time", xaxis_title="Month", yaxis_title=value_col)

    chart_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
    explanation = f"{value_col} is generally {direction} over the recorded period."

    return chart_html, explanation


def generate_ai_insights(summary, stats, kpis, dataset_type):
    """Sends your dataset's stats to Gemini and asks for plain-English business insights."""

    if not settings.GEMINI_API_KEY:
        return ["AI insights unavailable: no API key configured."]

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt = f"""
You are a business data analyst. Based on the following dataset summary, write 8 short,
specific, plain-English business insights. Each insight should be one sentence.
Do not repeat the raw numbers back verbatim - explain what they MEAN for the business.
Number them 1 to 8.

Dataset type: {dataset_type}
Total rows: {summary.get('total_rows')}
Total columns: {summary.get('total_columns')}
Descriptive statistics: {stats}
Business KPIs: {kpis}
"""

    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
        )
        text = response.text.strip()
        insights = [line.strip() for line in text.split('\n') if line.strip()]
        return insights
    except Exception as e:
        return [f"Could not generate AI insights: {e}"]


def detect_anomalies(df):
    """Flags numeric values that are unusually far from the average (basic outlier detection)."""

    anomalies = []
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns

    for col in numeric_cols:
        mean = df[col].mean()
        std = df[col].std()

        if std == 0 or pd.isna(std):
            continue

        outliers = df[(df[col] - mean).abs() > 2.5 * std]

        for idx, row in outliers.iterrows():
            anomalies.append({
                'column': col,
                'value': row[col],
                'row_number': idx + 1,
                'reason': f"far from the typical range (average is {round(mean, 2)})",
            })

    return anomalies[:10]


def forecast_next_period(df):
    """Simple forecast: predicts next month's value using average month-over-month growth."""

    date_col = None
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            date_col = col
            break

    if date_col is None:
        return None

    try:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    except Exception:
        return None

    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) == 0:
        return None

    value_col = numeric_cols[0]

    monthly = df.dropna(subset=[date_col]).sort_values(date_col)
    monthly = monthly.groupby(monthly[date_col].dt.to_period('M'))[value_col].sum()

    if len(monthly) < 2:
        return None

    growth_rates = monthly.pct_change().dropna()
    avg_growth = growth_rates.mean()

    last_value = monthly.iloc[-1]
    predicted_next = last_value * (1 + avg_growth)

    return {
        'metric': value_col,
        'last_period_value': round(last_value, 2),
        'predicted_next_value': round(predicted_next, 2),
        'avg_growth_rate_pct': round(avg_growth * 100, 2),
        'assumption': f"Assumes {value_col} continues its average month-over-month growth rate of {round(avg_growth * 100, 2)}%.",
    }


def generate_pdf_report(context):
    """Renders the report HTML template into a PDF and returns the PDF bytes."""
    from django.template.loader import render_to_string

    html = render_to_string('analyzer/report_template.html', context)
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer


def make_json_safe(obj):
    """Recursively converts numpy/pandas number types into plain Python types."""
    import numpy as np

    if isinstance(obj, dict):
        return {key: make_json_safe(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj