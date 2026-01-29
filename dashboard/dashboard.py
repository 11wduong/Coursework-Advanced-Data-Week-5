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
import queries

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


def load_summary_statistics():
    """Load summary statistics for all plants from today's readings."""
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
    WHERE CAST(recording_taken AS DATE) = CAST(GETDATE() AS DATE)
    """

    df = pd.read_sql(query, conn)
    return df.iloc[0]


def main():
    """Main dashboard application."""

    st.title("🌱 LNMH Plant Health Monitoring Dashboard")
    st.markdown("*Liverpool Natural History Museum - Botanical Conservatory*")
    st.markdown("---")

    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select View",
            ["Overview", "Real-Time Monitoring",
                "Plant Details", "Historical Analysis"]
        )

        st.markdown("---")
        st.header("📥 Download Historical Data")

        selected_date = st.date_input(
            "Select Date",
            value=datetime.now() - timedelta(days=1),
            min_value=datetime(2026, 1, 28),
            max_value=datetime.now() - timedelta(days=1),
            help="Download daily plant summary for the selected date"
        )

        s3_url = f"https://c21-boxen-botanical-archive.s3.eu-west-2.amazonaws.com/{selected_date.year:04d}/{selected_date.month:02d}/{selected_date.day:02d}/summary.csv"

        st.markdown(
            f"[📊 Download {selected_date.strftime('%Y-%m-%d')} Data]({s3_url})")
        st.caption(
            "Daily summaries include avg moisture & temperature for all plants")

    with st.spinner("🌱 Loading plant data..."):
        try:
            plants_df = load_plant_data()
            latest_readings = load_latest_readings()
            stats = load_summary_statistics()

            if page == "Overview":
                show_overview(stats, latest_readings, plants_df)
            elif page == "Real-Time Monitoring":
                show_realtime_monitoring(latest_readings)
            elif page == "Plant Details":
                show_plant_details(plants_df, latest_readings)
            elif page == "Historical Analysis":
                show_historical_analysis(plants_df)

        except Exception as e:
            st.info("🔄 Connecting to database...")
            st.caption("Waiting for database connection to be established.")


def show_overview(stats, latest_readings, plants_df):
    """Display overview page with key metrics."""
    st.header("📊 System Overview")

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

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Current Plant Health Status")

        if not latest_readings.empty:
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

    st.subheader("Recent Plant Readings")
    if not latest_readings.empty:
        display_df = latest_readings[[
            'plant_id', 'common_name', 'moisture', 'temperature',
            'recording_taken', 'botanist_name'
        ]].copy()

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

    plant_names = plants_df['common_name'].tolist()
    selected_plant = st.selectbox("Select a plant", plant_names)

    if selected_plant:
        plant_info = plants_df[plants_df['common_name']
                               == selected_plant].iloc[0]
        plant_id = plant_info['plant_id']

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
            latest = latest_readings[latest_readings['plant_id'] == plant_id]
            if not latest.empty:
                latest = latest.iloc[0]
                st.subheader("Latest Reading")
                st.write(f"**Moisture:** {latest['moisture']:.1f}%")
                st.write(f"**Temperature:** {latest['temperature']:.1f}°C")
                st.write(f"**Last Watered:** {latest['last_watered']}")
                st.write(f"**Recording Time:** {latest['recording_taken']}")
                st.write(f"**Botanist:** {latest['botanist_name']}")

                if latest['moisture'] < 20:
                    st.error("🔴 Critical - Needs immediate watering!")
                elif latest['moisture'] < 40:
                    st.warning("🟡 Warning - Monitor closely")
                else:
                    st.success("🟢 Healthy condition")

        st.subheader("📊 Compare with Other Plants (Today's Readings)")

        available_plants = [
            p for p in plants_df['common_name'].tolist() if p != selected_plant]
        selected_for_comparison = st.multiselect(
            "Select plants to compare with " + selected_plant,
            available_plants,
            default=available_plants[:2] if len(
                available_plants) >= 2 else available_plants
        )

        if selected_for_comparison:
            comparison_plants = [selected_plant] + selected_for_comparison

            plant_ids = plants_df[plants_df['common_name'].isin(
                comparison_plants)]['plant_id'].tolist()

            conn = get_db_connection()
            query = """
            SELECT 
                p.common_name,
                r.recording_taken,
                r.moisture,
                r.temperature
            FROM Record r
            INNER JOIN Plant p ON r.plant_id = p.plant_id
            WHERE p.plant_id IN ({})
            AND CAST(r.recording_taken AS DATE) = CAST(GETDATE() AS DATE)
            ORDER BY r.recording_taken
            """.format(','.join(['%s'] * len(plant_ids)))

            today_df = pd.read_sql(
                query, conn, params=tuple(plant_ids))

            if not today_df.empty:
                col1, col2 = st.columns(2)

                with col1:
                    fig = px.line(
                        today_df,
                        x='recording_taken',
                        y='moisture',
                        color='common_name',
                        title="Moisture Throughout Today",
                        labels={
                            'moisture': 'Moisture (%)', 'recording_taken': 'Time', 'common_name': 'Plant'}
                    )
                    fig.add_hline(y=40, line_dash="dash", line_color="orange",
                                  annotation_text="Optimal Minimum")
                    fig.add_hline(y=20, line_dash="dash", line_color="red",
                                  annotation_text="Critical Level")
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    fig = px.line(
                        today_df,
                        x='recording_taken',
                        y='temperature',
                        color='common_name',
                        title="Temperature Throughout Today",
                        labels={
                            'temperature': 'Temperature (°C)', 'recording_taken': 'Time', 'common_name': 'Plant'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No readings available for today")


def show_historical_analysis(plants_df):
    """Display historical analysis and trends from Athena."""
    st.header("📈 Historical Analysis")

    st.info("📊 Analysing historical data from archive...")

    days_back = st.slider("Days to analyse", 1, 90, 30,
                          help="Select number of days of historical data to display")

    try:
        config = queries.get_config()

        with st.spinner(f"Loading last {days_back} days of historical trends..."):
            moisture_trends = queries.query_moisture_trends(config, days_back)
            temp_trends = queries.query_temperature_trends(config, days_back)

        if not moisture_trends.empty and not temp_trends.empty:
            moisture_trends['date'] = pd.to_datetime(
                moisture_trends['date'], errors='coerce')
            moisture_trends = moisture_trends.dropna(subset=['date'])
            moisture_trends = moisture_trends.sort_values('date')
            moisture_trends['date_display'] = moisture_trends['date'].dt.strftime(
                '%Y-%m-%d')

            temp_trends['date'] = pd.to_datetime(
                temp_trends['date'], errors='coerce')
            temp_trends = temp_trends.dropna(subset=['date'])
            temp_trends = temp_trends.sort_values('date')
            temp_trends['date_display'] = temp_trends['date'].dt.strftime(
                '%Y-%m-%d')

            st.subheader(f"Historical Trends (Last {days_back} Days)")

            col1, col2 = st.columns(2)

            with col1:
                fig = px.line(
                    moisture_trends,
                    x='date_display',
                    y='avg_moisture',
                    title="Average Daily Moisture",
                    labels={
                        'avg_moisture': 'Moisture (%)', 'date_display': 'Date'},
                    markers=True
                )
                fig.add_hline(y=40, line_dash="dash", line_color="orange",
                              annotation_text="Optimal Minimum")
                fig.add_hline(y=20, line_dash="dash", line_color="red",
                              annotation_text="Critical Level")
                fig.update_xaxes(type='category')
                st.plotly_chart(fig, use_container_width=True)

                st.metric("Avg Moisture",
                          f"{moisture_trends['avg_moisture'].mean():.1f}%")
                st.metric("Min Moisture",
                          f"{moisture_trends['min_moisture'].min():.1f}%")
                st.metric("Max Moisture",
                          f"{moisture_trends['max_moisture'].max():.1f}%")

            with col2:
                fig = px.line(
                    temp_trends,
                    x='date_display',
                    y='avg_temperature',
                    title="Average Daily Temperature",
                    labels={
                        'avg_temperature': 'Temperature (°C)', 'date_display': 'Date'},
                    markers=True
                )
                fig.update_xaxes(type='category')
                st.plotly_chart(fig, use_container_width=True)

                st.metric("Avg Temperature",
                          f"{temp_trends['avg_temperature'].mean():.1f}°C")
                st.metric("Min Temperature",
                          f"{temp_trends['min_temperature'].min():.1f}°C")
                st.metric("Max Temperature",
                          f"{temp_trends['max_temperature'].max():.1f}°C")

        st.subheader("⚠️ Plants with Most Outliers")
        outliers = queries.query_outlier_analysis(config)

        if not outliers.empty:
            fig = px.bar(
                outliers,
                x='common_name',
                y=['total_temp_outliers', 'total_moisture_outliers'],
                title="Temperature and Moisture Outliers by Plant",
                labels={'value': 'Number of Outliers', 'common_name': 'Plant'},
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                outliers[['common_name', 'total_temp_outliers',
                          'total_moisture_outliers', 'days_recorded']],
                use_container_width=True,
                hide_index=True
            )

        st.subheader("🔴 Critical Plants (Historical Data)")
        critical = queries.query_critical_plants(config)

        if not critical.empty:
            st.warning(
                f"Found {len(critical)} plants with critical moisture levels")
            st.dataframe(
                critical[['plant_id', 'common_name', 'avg_moisture',
                          'avg_temperature', 'moisture_outliers']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success(
                "✅ No plants with critical moisture levels in historical data")

    except Exception as e:
        st.error(f"Error loading historical data from Athena: {str(e)}")
        st.info("Make sure Athena is configured and the Glue crawler has run.")


if __name__ == "__main__":
    main()
