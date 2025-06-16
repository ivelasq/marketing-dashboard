# Marketing Lead Quality Dashboard

An interactive Shiny for Python dashboard for analyzing marketing lead quality across different platforms (LinkedIn, TikTok, Events).

## Features

### Sidebar Filters
- **Date Range**: Filter leads by creation date
- **Platforms**: Select which marketing platforms to analyze
- **Company Size**: Filter by company employee count categories
- **Industries**: Multi-select industry filter
- **Lead Status**: Filter by lead progression status

### Key Metrics (KPI Cards)
- Total Leads
- Conversion Rate
- Average Deal Size
- Total Revenue

### Visualizations
1. **Lead Generation Trends**: Line chart showing lead volume over time by platform
2. **Platform Performance**: Combined bar/line chart showing average lead score vs conversion rate
3. **Conversion Funnel**: Bar chart showing lead progression by platform
4. **Lead Score Distribution**: Histogram of lead scores by platform
5. **Industry Performance**: Scatter plot showing lead score vs conversion rate by industry
6. **Revenue Analysis**: Revenue breakdown by company size and platform

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the dashboard:
```bash
python app.py
```

3. Open your browser to `http://localhost:8000`

## Technology Stack

- **Shiny for Python**: Interactive web application framework
- **Polars**: Fast DataFrame library for data processing
- **Plotnine**: Grammar of Graphics visualization library (ggplot2 for Python)
- **Matplotlib**: Backend for chart rendering

## Data Files

- `salesforce_leads.csv`: Lead data with platform attribution
- `platform_performance.csv`: Marketing platform metrics
- `lead_quality_metrics.csv`: Platform quality summaries
- `analysis_queries.sql`: SQL queries for data analysis

## Usage

The dashboard automatically loads the CSV data files and provides interactive filtering and visualization capabilities for marketing lead analysis.