"""
Liverpool Natural History Museum - Plant Health Monitoring Dashboard
Real-time visualization of plant sensor data from the botanical conservatory.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pymssql
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="LNMH Plant Monitor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def get_db_connection():
    """Create and return a database connection using environment variables."""
    load_dotenv()

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "1433")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    conn = pymssql.connect(
        server=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )

    return conn


def load_plant_data():
    """Load all plant information from the database."""
    conn = get_db_connection()

    query = """
    SELECT 
        p.plant_id,
        p.common_name,
        p.scientific_name,
        l.city,
        c.country,
        l.lat,
        l.long
    FROM Plant p
    LEFT JOIN Location l ON p.location_id = l.location_id
    LEFT JOIN Country c ON l.country_id = c.country_id
    ORDER BY p.plant_id
    """

    df = pd.read_sql(query, conn)
    return df


def load_latest_readings():
    """Load the most recent readings for all plants."""
    conn = get_db_connection()

    query = """
    SELECT 
        p.plant_id,
        p.common_name,
        p.scientific_name,
        r.moisture,
        r.temperature,
        r.recording_taken,
        r.last_watered,
        b.botanist_name,
        l.city,
        c.country
    FROM Record r
    INNER JOIN Plant p ON r.plant_id = p.plant_id
    LEFT JOIN Botanist b ON r.botanist_id = b.botanist_id
    LEFT JOIN Location l ON p.location_id = l.location_id
    LEFT JOIN Country c ON l.country_id = c.country_id
    WHERE r.recording_taken = (
        SELECT MAX(recording_taken) 
        FROM Record 
        WHERE plant_id = r.plant_id
    )
    ORDER BY p.plant_id
    """

    df = pd.read_sql(query, conn)
    return df


def load_plant_history(plant_id, days=7):
    """Load historical readings for a specific plant."""
    conn = get_db_connection()

    query = """
    SELECT 
        recording_taken,
        moisture,
        temperature,
        last_watered
    FROM Record
    WHERE plant_id = %s
    AND recording_taken >= DATEADD(day, -%s, GETDATE())
    ORDER BY recording_taken ASC
    """

    df = pd.read_sql(query, conn, params=(plant_id, days))
    return df


def load_summary_statistics():
    """Load summary statistics for all plants."""
    conn = get_db_connection()

    query = """
    SELECT 
        COUNT(DISTINCT plant_id) as total_plants,
        COUNT(*) as total_readings,
        AVG(moisture) as avg_moisture,
        AVG(temperature) as avg_temperature,
        MIN(recording_taken) as first_reading,
        MAX(recording_taken) as latest_reading
    FROM Record
    """

    df = pd.read_sql(query, conn)
    return df.iloc[0]


def main():
    """Main dashboard application."""

    # Header
    st.title("🌱 LNMH Plant Health Monitoring Dashboard")
    st.markdown("*Liverpool Natural History Museum - Botanical Conservatory*")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select View",
            ["Overview", "Real-Time Monitoring",
                "Plant Details", "Historical Analysis"]
        )

        st.markdown("---")
        st.header("📥 Download Historical Data")

        # Date picker for historical data
        selected_date = st.date_input(
            "Select Date",
            value=datetime.now() - timedelta(days=1),
            max_value=datetime.now() - timedelta(days=1),
            help="Download daily plant summary for the selected date"
        )

        # Generate S3 URL
        s3_url = f"https://c21-boxen-botanical-archive.s3.eu-west-2.amazonaws.com/{selected_date.year:04d}/{selected_date.month:02d}/{selected_date.day:02d}/summary.csv"

        # Download button
        st.markdown(
            f"[📊 Download {selected_date.strftime('%Y-%m-%d')} Data]({s3_url})")
        st.caption(
            "Daily summaries include avg moisture & temperature for all plants")

    # Load data with loading spinner
    with st.spinner("🌱 Loading plant data..."):
        try:
            plants_df = load_plant_data()
            latest_readings = load_latest_readings()
            stats = load_summary_statistics()

            # Page routing
            if page == "Overview":
                show_overview(stats, latest_readings, plants_df)
            elif page == "Real-Time Monitoring":
                show_realtime_monitoring(latest_readings)
            elif page == "Plant Details":
                show_plant_details(plants_df, latest_readings)
            elif page == "Historical Analysis":
                show_historical_analysis(plants_df)

        except Exception as e:
            # Show loading state on error to prevent showing error details
            st.info("🔄 Connecting to database...")
            st.caption("Waiting for database connection to be established.")


def show_overview(stats, latest_readings, plants_df):
    """Display overview page with key metrics."""
    st.header("📊 System Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Plants", int(stats['total_plants']))

    with col2:
        st.metric("Total Readings", f"{int(stats['total_readings']):,}")

    with col3:
        st.metric("Avg Moisture", f"{stats['avg_moisture']:.1f}%")

    with col4:
        st.metric("Avg Temperature", f"{stats['avg_temperature']:.1f}°C")

    st.markdown("---")

    # Current plant health status
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Current Plant Health Status")

        if not latest_readings.empty:
            # Health categories based on moisture
            latest_readings['health_status'] = latest_readings['moisture'].apply(
                lambda x: 'Critical' if x < 20 else (
                    'Warning' if x < 40 else 'Healthy')
            )

            status_counts = latest_readings['health_status'].value_counts()

            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Plant Health Distribution",
                color=status_counts.index,
                color_discrete_map={
                    'Healthy': '#28a745',
                    'Warning': '#ffc107',
                    'Critical': '#dc3545'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent readings available")

    with col2:
        st.subheader("Temperature vs Moisture")

        if not latest_readings.empty:
            fig = px.scatter(
                latest_readings,
                x='temperature',
                y='moisture',
                hover_data=['common_name'],
                title="Current Temperature vs Moisture Levels",
                labels={
                    'temperature': 'Temperature (°C)', 'moisture': 'Moisture (%)'}
            )
            fig.add_hline(y=40, line_dash="dash", line_color="orange",
                          annotation_text="Min. Healthy Moisture")
            fig.add_hline(y=20, line_dash="dash", line_color="red",
                          annotation_text="Critical Moisture")
            st.plotly_chart(fig, use_container_width=True)

    # Recent readings table
    st.subheader("Recent Plant Readings")
    if not latest_readings.empty:
        display_df = latest_readings[[
            'plant_id', 'common_name', 'moisture', 'temperature',
            'recording_taken', 'botanist_name'
        ]].copy()

        # Add health indicator
        display_df['status'] = display_df['moisture'].apply(
            lambda x: '🔴' if x < 20 else ('🟡' if x < 40 else '🟢')
        )

        st.dataframe(display_df, use_container_width=True, hide_index=True)


def show_realtime_monitoring(latest_readings):
    """Display real-time monitoring page."""
    st.header("⚡ Real-Time Plant Monitoring")

    if latest_readings.empty:
        st.warning("No real-time data available")
        return

    # Moisture levels chart
    st.subheader("Current Moisture Levels by Plant")
    fig = px.bar(
        latest_readings.sort_values('moisture'),
        x='common_name',
        y='moisture',
        color='moisture',
        title="Soil Moisture Levels",
        labels={'moisture': 'Moisture (%)', 'common_name': 'Plant'},
        color_continuous_scale=['red', 'yellow', 'green']
    )
    fig.add_hline(y=40, line_dash="dash", line_color="orange",
                  annotation_text="Optimal Minimum")
    fig.add_hline(y=20, line_dash="dash", line_color="red",
                  annotation_text="Critical Level")
    st.plotly_chart(fig, use_container_width=True)

    # Temperature levels chart
    st.subheader("Current Temperature Levels by Plant")
    fig = px.bar(
        latest_readings.sort_values('temperature'),
        x='common_name',
        y='temperature',
        color='temperature',
        title="Temperature Readings",
        labels={'temperature': 'Temperature (°C)', 'common_name': 'Plant'},
        color_continuous_scale='Reds'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Alert section
    st.subheader("⚠️ Alerts & Warnings")

    critical_plants = latest_readings[latest_readings['moisture'] < 20]
    warning_plants = latest_readings[(latest_readings['moisture'] >= 20) & (
        latest_readings['moisture'] < 40)]

    if not critical_plants.empty:
        st.error(
            f"🔴 **CRITICAL**: {len(critical_plants)} plants need immediate attention!")
        st.dataframe(
            critical_plants[['common_name', 'moisture',
                             'temperature', 'last_watered', 'botanist_name']],
            use_container_width=True,
            hide_index=True
        )

    if not warning_plants.empty:
        st.warning(
            f"🟡 **WARNING**: {len(warning_plants)} plants require monitoring")
        st.dataframe(
            warning_plants[['common_name', 'moisture',
                            'temperature', 'last_watered', 'botanist_name']],
            use_container_width=True,
            hide_index=True
        )

    if critical_plants.empty and warning_plants.empty:
        st.success("✅ All plants are in healthy condition!")


def show_plant_details(plants_df, latest_readings):
    """Display detailed information for individual plants."""
    st.header("🔍 Plant Details")

    if plants_df.empty:
        st.warning("No plants found in database")
        return

    # Plant selector
    plant_names = plants_df['common_name'].tolist()
    selected_plant = st.selectbox("Select a plant", plant_names)

    if selected_plant:
        plant_info = plants_df[plants_df['common_name']
                               == selected_plant].iloc[0]
        plant_id = plant_info['plant_id']

        # Display plant information
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Plant Information")
            st.write(f"**Common Name:** {plant_info['common_name']}")
            st.write(f"**Scientific Name:** {plant_info['scientific_name']}")
            st.write(f"**Plant ID:** {plant_id}")
            st.write(
                f"**Origin:** {plant_info['city']}, {plant_info['country']}")
            if pd.notna(plant_info['lat']) and pd.notna(plant_info['long']):
                st.write(
                    f"**Coordinates:** {plant_info['lat']:.4f}, {plant_info['long']:.4f}")

        with col2:
            # Latest reading
            latest = latest_readings[latest_readings['plant_id'] == plant_id]
            if not latest.empty:
                latest = latest.iloc[0]
                st.subheader("Latest Reading")
                st.write(f"**Moisture:** {latest['moisture']:.1f}%")
                st.write(f"**Temperature:** {latest['temperature']:.1f}°C")
                st.write(f"**Last Watered:** {latest['last_watered']}")
                st.write(f"**Recording Time:** {latest['recording_taken']}")
                st.write(f"**Botanist:** {latest['botanist_name']}")

                # Health indicator
                if latest['moisture'] < 20:
                    st.error("🔴 Critical - Needs immediate watering!")
                elif latest['moisture'] < 40:
                    st.warning("🟡 Warning - Monitor closely")
                else:
                    st.success("🟢 Healthy condition")

        # Show recent history
        st.subheader("Recent History (Last 7 Days)")
        days_select = st.slider("Select number of days", 1, 30, 7)
        history = load_plant_history(plant_id, days_select)

        if not history.empty:
            col1, col2 = st.columns(2)

            with col1:
                fig = px.line(
                    history,
                    x='recording_taken',
                    y='moisture',
                    title="Moisture Over Time",
                    labels={
                        'moisture': 'Moisture (%)', 'recording_taken': 'Date'}
                )
                fig.add_hline(y=40, line_dash="dash", line_color="orange")
                fig.add_hline(y=20, line_dash="dash", line_color="red")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.line(
                    history,
                    x='recording_taken',
                    y='temperature',
                    title="Temperature Over Time",
                    labels={
                        'temperature': 'Temperature (°C)', 'recording_taken': 'Date'}
                )
                st.plotly_chart(fig, use_container_width=True)


def show_historical_analysis(plants_df):
    """Display historical analysis and trends."""
    st.header("📈 Historical Analysis")

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        days_back = st.slider("Analysis Period (days)", 1, 90, 30)

    conn = get_db_connection()

    # Load historical data
    query = """
    SELECT 
        p.plant_id,
        p.common_name,
        r.recording_taken,
        r.moisture,
        r.temperature
    FROM Record r
    INNER JOIN Plant p ON r.plant_id = p.plant_id
    WHERE r.recording_taken >= DATEADD(day, -%s, GETDATE())
    ORDER BY r.recording_taken
    """

    history_df = pd.read_sql(query, conn, params=(days_back,))

    if history_df.empty:
        st.warning("No historical data available for the selected period")
        return

    # Average trends over time
    st.subheader("Average Conditions Over Time")

    daily_avg = history_df.groupby(history_df['recording_taken'].dt.date).agg({
        'moisture': 'mean',
        'temperature': 'mean'
    }).reset_index()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(
            daily_avg,
            x='recording_taken',
            y='moisture',
            title="Average Daily Moisture",
            labels={'moisture': 'Moisture (%)', 'recording_taken': 'Date'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(
            daily_avg,
            x='recording_taken',
            y='temperature',
            title="Average Daily Temperature",
            labels={
                'temperature': 'Temperature (°C)', 'recording_taken': 'Date'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Plant comparison
    st.subheader("Plant Comparison")

    selected_plants = st.multiselect(
        "Select plants to compare",
        plants_df['common_name'].tolist(),
        default=plants_df['common_name'].tolist()[:3]
    )

    if selected_plants:
        filtered_history = history_df[history_df['common_name'].isin(
            selected_plants)]

        col1, col2 = st.columns(2)

        with col1:
            fig = px.line(
                filtered_history,
                x='recording_taken',
                y='moisture',
                color='common_name',
                title="Moisture Comparison",
                labels={'moisture': 'Moisture (%)', 'recording_taken': 'Date'}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                filtered_history,
                x='recording_taken',
                y='temperature',
                color='common_name',
                title="Temperature Comparison",
                labels={
                    'temperature': 'Temperature (°C)', 'recording_taken': 'Date'}
            )
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
