# LNMH Plant Health Monitoring Dashboard

A Streamlit dashboard for monitoring plant health in the Liverpool Natural History Museum's botanical conservatory.

## Features

- **Overview**: Key metrics, health status distribution, and recent readings
- **Real-Time Monitoring**: Live moisture and temperature levels with alerts
- **Plant Details**: Individual plant information and 7-day history
- **Historical Analysis**: Trends and comparisons over time (up to 90 days)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the `.env` file is configured in the `archive_pipeline` directory with your database credentials:
```
DB_HOST=your_host
DB_PORT=1433
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=plants
```

The dashboard uses the same database connection from `archive_pipeline/extract.py`.

## Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Health Indicators

- 🟢 **Healthy**: Moisture ≥ 40%
- 🟡 **Warning**: 20% ≤ Moisture < 40%
- 🔴 **Critical**: Moisture < 20%

## Features Detail

### Overview Page
- Total plants and readings statistics
- Average moisture and temperature across all plants
- Health status pie chart
- Temperature vs moisture scatter plot
- Recent readings table with status indicators

### Real-Time Monitoring
- Bar charts for current moisture and temperature levels
- Alert section highlighting critical and warning plants
- Botanist responsible for each plant

### Plant Details
- Select individual plants to view detailed information
- Origin location and coordinates
- Latest sensor readings
- Historical graphs for moisture and temperature
- Adjustable time range (1-30 days)

### Historical Analysis
- Long-term trends (up to 90 days)
- Daily average moisture and temperature
- Multi-plant comparison charts
- Identify patterns and anomalies

## Auto-Refresh

Enable the "Auto-refresh" option in the sidebar to automatically update the dashboard every 30 seconds.
