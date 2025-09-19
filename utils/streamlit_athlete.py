import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

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

def load_elo_data():
    """Load ELO history data if available."""
    try:
        elo_file = Path("Elo_Data/elo_history.csv")
        if elo_file.exists():
            return pd.read_csv(elo_file, parse_dates=['date'])
        return None
    except Exception as e:
        return None

def render():
    """Render the athlete analytics dashboard."""
    
    st.header("Athlete Performance Analytics")
    
    # Load data
    df = load_data()
    elo_df = load_elo_data()
    
    if df is None or df.empty:
        st.error("No competition data available")
        return
    
    # Clean and prepare data
    df = df.dropna(subset=['name', 'year', 'discipline', 'gender'])
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df = df.dropna(subset=['year'])
    
    if 'start_date' in df.columns:
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    
    if 'round_rank' in df.columns:
        df['round_rank'] = pd.to_numeric(df['round_rank'], errors='coerce')
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Individual Analysis",
        "Head-to-Head", 
        "Career Progression",
        "Discipline Crossover",
        "Location Performance"
    ])
    
    with tab1:
        render_individual_analysis(df, elo_df)
    
    with tab2:
        render_head_to_head(df, elo_df)
    
    with tab3:
        render_career_progression(df, elo_df)
    
    with tab4:
        render_discipline_crossover(df)
    
    with tab5:
        render_location_performance(df)

def render_individual_analysis(df, elo_df):
    """Render individual athlete analysis."""
    
    st.subheader("Individual Athlete Deep Dive")
    
    # Athlete selection
    athletes = sorted(df['name'].unique())
    selected_athlete = st.selectbox("Select Athlete", athletes)
    
    if not selected_athlete:
        return
    
    # Filter data for selected athlete
    athlete_df = df[df['name'] == selected_athlete].copy()
    
    if athlete_df.empty:
        st.warning(f"No data found for {selected_athlete}")
        return
    
    # Basic athlete info
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_comps = len(athlete_df)
        st.metric("Total Competitions", total_comps)
    
    with col2:
        disciplines = athlete_df['discipline'].nunique()
        st.metric("Disciplines", disciplines)
    
    with col3:
        countries = athlete_df['country'].nunique() if 'country' in athlete_df.columns else 1
        st.metric("Countries Competed", countries)
    
    with col4:
        years_active = athlete_df['year'].max() - athlete_df['year'].min() + 1
        st.metric("Years Active", years_active)
    
    # Performance overview
    if 'round_rank' in athlete_df.columns:
        rank_data = athlete_df.dropna(subset=['round_rank'])
        
        if not rank_data.empty:
            col_perf1, col_perf2, col_perf3 = st.columns(3)
            
            with col_perf1:
                avg_rank = rank_data['round_rank'].mean()
                st.metric("Average Rank", f"{avg_rank:.1f}")
            
            with col_perf2:
                podiums = (rank_data['round_rank'] <= 3).sum()
                st.metric("Podium Finishes", podiums)
            
            with col_perf3:
                wins = (rank_data['round_rank'] == 1).sum()
                st.metric("Wins", wins)
    
    # Competition timeline
    st.subheader("Competition Timeline")
    
    if 'start_date' in athlete_df.columns:
        timeline_df = athlete_df.dropna(subset=['start_date']).copy()
        timeline_df = timeline_df.sort_values('start_date')
        
        if 'round_rank' in timeline_df.columns:
            fig_timeline = px.scatter(
                timeline_df,
                x='start_date',
                y='round_rank',
                color='discipline',
                size_max=10,
                title=f"{selected_athlete} - Competition Results Over Time",
                hover_data=['event_name', 'location'] if 'event_name' in timeline_df.columns else None
            )
            # fig_timeline.update_yaxis(autorange="reversed")
            fig_timeline.update_layout(height=500)
            st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Performance by discipline
    if len(athlete_df['discipline'].unique()) > 1:
        st.subheader("Performance by Discipline")
        
        discipline_stats = athlete_df.groupby('discipline').agg({
            'round_rank': ['count', 'mean', 'min'] if 'round_rank' in athlete_df.columns else ['count'],
            'year': ['min', 'max']
        }).round(2)
        
        discipline_stats.columns = ['_'.join(col).strip() for col in discipline_stats.columns.values]
        discipline_stats = discipline_stats.reset_index()
        
        st.dataframe(discipline_stats, use_container_width=True)
    
    # ELO progression if available
    if elo_df is not None:
        athlete_elo = elo_df[
            (elo_df['name'].str.lower() == selected_athlete.lower()) &
            (elo_df['competed'] == True)
        ].copy()
        
        if not athlete_elo.empty:
            st.subheader("ELO Rating Progression")
            
            fig_elo = px.line(
                athlete_elo,
                x='date',
                y='elo_after',
                color='discipline',
                title=f"{selected_athlete} - ELO Rating History",
                markers=True
            )
            fig_elo.update_layout(height=400)
            st.plotly_chart(fig_elo, use_container_width=True)

def render_head_to_head(df, elo_df):
    """Render head-to-head athlete comparison."""
    
    st.subheader("Head-to-Head Comparison")
    
    athletes = sorted(df['name'].unique())
    
    col1, col2 = st.columns(2)
    with col1:
        athlete1 = st.selectbox("Select First Athlete", athletes, key="h2h_athlete1")
    with col2:
        athlete2 = st.selectbox("Select Second Athlete", athletes, key="h2h_athlete2")
    
    if not athlete1 or not athlete2 or athlete1 == athlete2:
        st.info("Please select two different athletes to compare")
        return
    
    # Get data for both athletes
    athlete1_df = df[df['name'] == athlete1].copy()
    athlete2_df = df[df['name'] == athlete2].copy()
    
    # Comparison metrics
    st.subheader("Comparison Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**{athlete1}**")
        st.metric("Total Competitions", len(athlete1_df))
        if 'round_rank' in athlete1_df.columns:
            rank_data1 = athlete1_df.dropna(subset=['round_rank'])
            if not rank_data1.empty:
                st.metric("Average Rank", f"{rank_data1['round_rank'].mean():.1f}")
                st.metric("Wins", (rank_data1['round_rank'] == 1).sum())
                st.metric("Podiums", (rank_data1['round_rank'] <= 3).sum())
    
    with col2:
        st.write(f"**{athlete2}**")
        st.metric("Total Competitions", len(athlete2_df))
        if 'round_rank' in athlete2_df.columns:
            rank_data2 = athlete2_df.dropna(subset=['round_rank'])
            if not rank_data2.empty:
                st.metric("Average Rank", f"{rank_data2['round_rank'].mean():.1f}")
                st.metric("Wins", (rank_data2['round_rank'] == 1).sum())
                st.metric("Podiums", (rank_data2['round_rank'] <= 3).sum())
    
    # Direct matchups
    st.subheader("Direct Matchups")
    
    if 'event_name' in df.columns and 'round_rank' in df.columns:
        # Find events where both competed
        common_events = set(athlete1_df['event_name'].unique()) & set(athlete2_df['event_name'].unique())
        
        if common_events:
            matchups = []
            for event in common_events:
                event_data1 = athlete1_df[athlete1_df['event_name'] == event]
                event_data2 = athlete2_df[athlete2_df['event_name'] == event]
                
                if not event_data1.empty and not event_data2.empty:
                    rank1 = event_data1['round_rank'].iloc[0] if 'round_rank' in event_data1.columns else None
                    rank2 = event_data2['round_rank'].iloc[0] if 'round_rank' in event_data2.columns else None
                    
                    if pd.notna(rank1) and pd.notna(rank2):
                        matchups.append({
                            'Event': event,
                            f'{athlete1} Rank': int(rank1),
                            f'{athlete2} Rank': int(rank2),
                            'Winner': athlete1 if rank1 < rank2 else athlete2 if rank2 < rank1 else 'Tie'
                        })
            
            if matchups:
                matchup_df = pd.DataFrame(matchups)
                st.dataframe(matchup_df, use_container_width=True)
                
                # Head-to-head record
                wins1 = (matchup_df['Winner'] == athlete1).sum()
                wins2 = (matchup_df['Winner'] == athlete2).sum()
                ties = (matchup_df['Winner'] == 'Tie').sum()
                
                st.write(f"**Head-to-Head Record**: {athlete1} {wins1} - {wins2} {athlete2} (Ties: {ties})")
            else:
                st.info("No direct matchups found with ranking data")
        else:
            st.info("These athletes haven't competed in the same events")

def render_career_progression(df, elo_df):
    """Render career progression analysis."""
    
    st.subheader("Career Progression Analysis")
    
    # Select athlete
    athletes = sorted(df['name'].unique())
    selected_athlete = st.selectbox("Select Athlete for Career Analysis", athletes, key="career_athlete")
    
    if not selected_athlete:
        return
    
    athlete_df = df[df['name'] == selected_athlete].copy()
    
    if athlete_df.empty:
        st.warning(f"No data found for {selected_athlete}")
        return
    
    # Career phases analysis
    if 'round_rank' in athlete_df.columns and 'year' in athlete_df.columns:
        rank_data = athlete_df.dropna(subset=['round_rank', 'year']).copy()
        
        if not rank_data.empty:
            # Calculate rolling averages
            yearly_performance = rank_data.groupby('year').agg({
                'round_rank': ['mean', 'count', 'min'],
                'name': 'count'
            }).round(2)
            
            yearly_performance.columns = ['avg_rank', 'competitions', 'best_rank', 'total_entries']
            yearly_performance = yearly_performance.reset_index()
            
            # Career progression chart
            fig_career = go.Figure()
            
            fig_career.add_trace(go.Scatter(
                x=yearly_performance['year'],
                y=yearly_performance['avg_rank'],
                mode='lines+markers',
                name='Average Rank',
                line=dict(width=3)
            ))
            
            fig_career.add_trace(go.Scatter(
                x=yearly_performance['year'],
                y=yearly_performance['best_rank'],
                mode='markers',
                name='Best Rank',
                marker=dict(size=8, symbol='star')
            ))
            
            fig_career.update_layout(
                title=f"{selected_athlete} - Career Progression",
                xaxis_title="Year",
                yaxis_title="Rank (Lower is Better)",
                yaxis=dict(autorange="reversed"),
                height=500
            )
            
            st.plotly_chart(fig_career, use_container_width=True)
            
            # Peak performance identification
            st.subheader("Peak Performance Analysis")
            
            best_year = yearly_performance.loc[yearly_performance['avg_rank'].idxmin()]
            most_active_year = yearly_performance.loc[yearly_performance['competitions'].idxmax()]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Best Performance Year**")
                st.write(f"Year: {int(best_year['year'])}")
                st.write(f"Average Rank: {best_year['avg_rank']:.1f}")
                st.write(f"Competitions: {int(best_year['competitions'])}")
            
            with col2:
                st.write("**Most Active Year**")
                st.write(f"Year: {int(most_active_year['year'])}")
                st.write(f"Competitions: {int(most_active_year['competitions'])}")
                st.write(f"Average Rank: {most_active_year['avg_rank']:.1f}")

def render_discipline_crossover(df):
    """Render discipline crossover analysis."""
    
    st.subheader("Discipline Crossover Analysis")
    
    # Find athletes who compete in multiple disciplines
    athlete_disciplines = df.groupby('name')['discipline'].nunique().reset_index()
    multi_discipline = athlete_disciplines[athlete_disciplines['discipline'] > 1]
    
    if multi_discipline.empty:
        st.info("No athletes found competing in multiple disciplines")
        return
    
    st.write(f"Found {len(multi_discipline)} athletes competing in multiple disciplines")
    
    # Show crossover statistics
    crossover_stats = df[df['name'].isin(multi_discipline['name'])].groupby('name').agg({
        'discipline': lambda x: ', '.join(sorted(x.unique())),
        'round_rank': 'mean' if 'round_rank' in df.columns else 'count',
        'year': ['min', 'max']
    }).round(2)
    
    crossover_stats.columns = ['Disciplines', 'Avg_Rank', 'First_Year', 'Last_Year']
    crossover_stats = crossover_stats.reset_index()
    crossover_stats = crossover_stats.sort_values('Avg_Rank' if 'round_rank' in df.columns else 'First_Year')
    
    st.dataframe(crossover_stats, use_container_width=True)
    
    # Discipline combination analysis
    st.subheader("Most Common Discipline Combinations")
    
    discipline_combinations = crossover_stats['Disciplines'].value_counts().head(10)
    
    fig_combinations = px.bar(
        x=discipline_combinations.values,
        y=discipline_combinations.index,
        orientation='h',
        title='Most Common Discipline Combinations',
        labels={'x': 'Number of Athletes', 'y': 'Discipline Combination'}
    )
    fig_combinations.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_combinations, use_container_width=True)

def render_location_performance(df):
    """Render location-based performance analysis."""
    
    st.subheader("Location Performance Analysis")
    
    if 'location' not in df.columns:
        st.warning("Location data not available")
        return
    
    location_df = df.dropna(subset=['location']).copy()
    
    if location_df.empty:
        st.warning("No location data found")
        return
    
    # Athlete selection
    athletes = sorted(location_df['name'].unique())
    selected_athlete = st.selectbox("Select Athlete for Location Analysis", athletes, key="location_athlete")
    
    if not selected_athlete:
        return
    
    athlete_location_df = location_df[location_df['name'] == selected_athlete].copy()
    
    if athlete_location_df.empty:
        st.warning(f"No location data found for {selected_athlete}")
        return
    
    # Performance by location
    if 'round_rank' in athlete_location_df.columns:
        location_performance = athlete_location_df.groupby('location').agg({
            'round_rank': ['mean', 'count', 'min'],
            'year': ['min', 'max']
        }).round(2)
        
        location_performance.columns = ['avg_rank', 'competitions', 'best_rank', 'first_year', 'last_year']
        location_performance = location_performance.reset_index()
        location_performance = location_performance[location_performance['competitions'] >= 2]  # Filter for meaningful sample
        
        if not location_performance.empty:
            # Best and worst performing locations
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Best Performing Locations")
                best_locations = location_performance.nsmallest(5, 'avg_rank')
                
                fig_best = px.bar(
                    best_locations,
                    x='avg_rank',
                    y='location',
                    orientation='h',
                    title='Best Average Rankings by Location',
                    labels={'avg_rank': 'Average Rank', 'location': 'Location'}
                )
                fig_best.update_layout(height=400, yaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig_best, use_container_width=True)
            
            with col2:
                st.subheader("Most Competed Locations")
                most_competed = location_performance.nlargest(5, 'competitions')
                
                fig_most = px.bar(
                    most_competed,
                    x='competitions',
                    y='location',
                    orientation='h',
                    title='Most Competitions by Location',
                    labels={'competitions': 'Number of Competitions', 'location': 'Location'}
                )
                fig_most.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_most, use_container_width=True)
            
            # Detailed location statistics
            st.subheader("Detailed Location Statistics")
            st.dataframe(location_performance.sort_values('avg_rank'), use_container_width=True)
    
    # Global performance trends
    st.subheader("Global Performance Trends")
    
    # Overall location statistics
    global_location_stats = location_df.groupby('location').agg({
        'name': 'nunique',
        'round_rank': 'mean' if 'round_rank' in location_df.columns else 'count',
        'year': ['min', 'max']
    }).round(2)
    
    global_location_stats.columns = ['unique_athletes', 'avg_rank', 'first_event', 'last_event']
    global_location_stats = global_location_stats.reset_index()
    global_location_stats = global_location_stats[global_location_stats['unique_athletes'] >= 10]
    
    if not global_location_stats.empty:
        # Most competitive locations (by average rank)
        competitive_locations = global_location_stats.nsmallest(10, 'avg_rank')
        
        fig_competitive = px.scatter(
            competitive_locations,
            x='unique_athletes',
            y='avg_rank',
            size='unique_athletes',
            hover_name='location',
            title='Most Competitive Locations (Lower Avg Rank = More Competitive)',
            labels={'unique_athletes': 'Number of Athletes', 'avg_rank': 'Average Rank'}
        )
        fig_competitive.update_layout(height=500)
        st.plotly_chart(fig_competitive, use_container_width=True)