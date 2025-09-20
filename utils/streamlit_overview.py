import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import numpy as np

def load_data():
    """Load aggregated competition data."""
    try:
        data_file = Path("Data/aggregate_data/aggregated_results.csv")
        if not data_file.exists():
            return None
        return pd.read_csv(data_file)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def render():
    """Render the overview dashboard with comprehensive statistics."""
    
    st.header("Competition Overview Dashboard")
    
    # Load data
    df = load_data()
    if df is None or df.empty:
        st.error("No competition data available")
        return
    
    # Clean and prepare data
    df = df.dropna(subset=['name', 'year', 'discipline', 'gender'])
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df = df.dropna(subset=['year'])
    
    # Overview metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_records = len(df)
        st.metric("Total Competitions", f"{total_records:,}")
    
    with col2:
        unique_athletes = df['name'].nunique()
        st.metric("Unique Athletes", f"{unique_athletes:,}")
    
    with col3:
        unique_countries = df['country'].nunique() if 'country' in df.columns else 0
        st.metric("Countries", f"{unique_countries:,}")
    
    with col4:
        year_span = f"{int(df['year'].min())}-{int(df['year'].max())}"
        st.metric("Year Range", year_span)
    
    # Create two columns for charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Competitions by year and discipline
        st.subheader("Competitions Over Time")
        yearly_discipline = df.groupby(['year', 'discipline']).size().reset_index(name='count')
        
        fig_yearly = px.line(
            yearly_discipline,
            x='year',
            y='count',
            color='discipline',
            title='Competition Count by Discipline Over Time',
            markers=True
        )
        fig_yearly.update_layout(height=400)
        st.plotly_chart(fig_yearly, width='stretch')
        
        # Gender participation over time
        st.subheader("Gender Participation")
        yearly_gender = df.groupby(['year', 'gender']).size().reset_index(name='count')
        
        fig_gender = px.area(
            yearly_gender,
            x='year',
            y='count',
            color='gender',
        )
        fig_gender.update_layout(height=400)
        st.plotly_chart(fig_gender, width='stretch')
    
    with col_right:
        # Discipline distribution pie chart
        st.subheader("Competition Distribution")
        discipline_counts = df['discipline'].value_counts()
        
        fig_pie = px.pie(
            values=discipline_counts.values,
            names=discipline_counts.index,
            title='Competitions by Discipline'
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, width='stretch')
        
        # Top countries by participation
        if 'country' in df.columns:
            st.subheader("Top Participating Countries")
            country_counts = df['country'].value_counts().head(10)
            
            fig_countries = px.bar(
                x=country_counts.values,
                y=country_counts.index,
                orientation='h',
            )
            fig_countries.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_countries, width='stretch')
    
    # Full width charts
    st.subheader("Detailed Analytics")
    
    # Athletes per competition over time
    athletes_per_comp =  df[~df['discipline'].isin(['Boulder&lead', 'Combined'])].groupby(['year', 'discipline']).agg({
        'name': 'nunique',
        'event_name': 'nunique'
    }).reset_index()
    athletes_per_comp['avg_athletes'] = athletes_per_comp['name'] / athletes_per_comp['event_name']
    
    fig_athletes = px.line(
        athletes_per_comp,
        x='year',
        y='avg_athletes',
        color='discipline',
        title='Average Athletes per Competition by Discipline',
        markers=True
    )
    fig_athletes.update_layout(height=400)
    st.plotly_chart(fig_athletes, width='stretch')
    
    # Scoring system evolution
    era_colors = {
        "Boulder_UIAA_Legacy_1991-2006": "#08519c", # dark blue,
        "Boulder_IFSC_AddedPoints_2025-2025": "#3182bd", # medium blue
        "Boulder_IFSC_ZoneTop_2007-2024": "#6baed6", # light blue

        "Lead_UIAA_Legacy_1991-2006": "#cb181d", # dark red
        "Lead_IFSC_Modern_2007-2025": "#e6775f", # medium red

        "Speed_UIAA_Legacy_1991-2006": "#238b45", # dark green
        "Speed_IFSC_Score_2007-2008": "#41ae76", # medium green
        "Speed_IFSC_Time_2009-2025": "#74aa6e", # light green
        
        }
    if 'scoring_era' in df.columns:
        st.subheader("Scoring System Evolution")
        era_timeline = df[~df['discipline'].isin(['Boulder&lead', 'Combined'])].groupby(['year', 'scoring_era']).size().reset_index(name='count')
        
        fig_eras = px.bar(
            era_timeline,
            x='year',
            y='count',
            color="scoring_era",
            color_discrete_map=era_colors,
            title='Competition Count by Scoring System Over Time'
        )
        fig_eras.update_layout(height=400)
        st.plotly_chart(fig_eras, width='stretch')
    
    # Event frequency heatmap
    if 'start_date' in df.columns:
        st.subheader("Competition Calendar Heatmap")
        
        # Convert dates and extract month
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
        df_with_dates = df.dropna(subset=['start_date'])
        
        if not df_with_dates.empty:
            df_with_dates['month'] = df_with_dates['start_date'].dt.month
            monthly_counts = df_with_dates.groupby(['year', 'month']).size().reset_index(name='competitions')
            
            # Create pivot for heatmap
            heatmap_data = monthly_counts.pivot(index='year', columns='month', values='competitions').fillna(0)
            
            fig_heatmap = px.imshow(
                heatmap_data,
                labels=dict(x="Month", y="Year", color="Competitions"),
                title="Competition Frequency by Month and Year",
                aspect="auto"
            )
            fig_heatmap.update_layout(height=500)
            st.plotly_chart(fig_heatmap, width='stretch')
    
   