# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# from pathlib import Path
# import numpy as np
# from datetime import datetime, timedelta

# def load_data():
#     """Load aggregated competition data."""
#     try:
#         data_file = Path("Data/aggregate_data/aggregated_results.csv")
#         if not data_file.exists():
#             return None
#         return pd.read_csv(data_file)
#     except Exception as e:
#         st.error(f"Error loading data: {e}")
#         return None

# def load_elo_data():
#     """Load ELO history data if available."""
#     try:
#         elo_file = Path("Elo_Data/elo_history.csv")
#         if elo_file.exists():
#             return pd.read_csv(elo_file, parse_dates=['date'])
#         return None
#     except Exception as e:
#         return None

# def render():
#     """Render the athlete analytics dashboard."""
    
#     st.header("Athlete Performance Analytics")
    
#     # Load data
#     df = load_data()
#     elo_df = load_elo_data()
    
#     if df is None or df.empty:
#         st.error("No competition data available")
#         return
    
#     # Clean and prepare data
#     df = df.dropna(subset=['name', 'year', 'discipline', 'gender'])
#     df['year'] = pd.to_numeric(df['year'], errors='coerce')
#     df = df.dropna(subset=['year'])
    
#     if 'start_date' in df.columns:
#         df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    
#     if 'round_rank' in df.columns:
#         df['round_rank'] = pd.to_numeric(df['round_rank'], errors='coerce')
    
#     render_individual_analysis(df, elo_df)
    
#     render_head_to_head(df, elo_df)

#     render_location_performance(df)

# def render_individual_analysis(df, elo_df):
#     """Render individual athlete analysis."""
        
#     # Athlete selection
#     athletes = sorted(df['name'].unique())
#     default_athlete = "Ondra Adam" if "Ondra Adam" in athletes else athletes[0]
#     selected_athlete = st.selectbox("Select Athlete", athletes, index=athletes.index(default_athlete) if default_athlete in athletes else 0)
    
#     #### move second athlete for comparison to here ###

#     if not selected_athlete:
#         return
    
#     # Filter data for selected athlete
#     athlete_df = df[df['name'] == selected_athlete].copy()
    
#     if athlete_df.empty:
#         st.warning(f"No data found for {selected_athlete}")
#         return
    
#     # Basic athlete info
#     col0, col1, col2, col3, col4, col5 = st.columns(6)
#     with col0:
#         st.metric("Current ELO", 
#                   f"{elo_df[elo_df['name'] == selected_athlete]['elo_after'].iloc[-1]:.0f}" if elo_df is not None and not elo_df[elo_df['name'] == selected_athlete].empty else "N/A")

#     with col1:
#         total_comps = len(athlete_df)
#         st.metric("Total Competitions", total_comps)
  
#     with col2:
#         years_active = athlete_df['year'].max() - athlete_df['year'].min() + 1
#         st.metric("Years Active", years_active)
    
#     # Performance overview
#     if 'round_rank' in athlete_df.columns:
#         rank_data = athlete_df.dropna(subset=['round_rank'])
        
#         if not rank_data.empty:
           
#             with col3:
#                 avg_rank = rank_data['round_rank'].mean()
#                 st.metric("Average Rank", f"{avg_rank:.1f}")
            
#             with col4:
#                 podiums = (rank_data['round_rank'] <= 3).sum()
#                 st.metric("Podium Finishes", podiums)
            
#             with col5:
#                 wins = (rank_data['round_rank'] == 1).sum()
#                 st.metric("Wins", wins)
    
#     # Competition timeline
#     st.subheader("Competition Timeline")
    
#     if 'start_date' in athlete_df.columns:
#         timeline_df = athlete_df.dropna(subset=['start_date']).copy()
#         timeline_df = timeline_df.sort_values('start_date')
        
#         if 'round_rank' in timeline_df.columns:
#             fig_timeline = px.scatter(
#                 timeline_df,
#                 x='start_date',
#                 y='round_rank',
#                 color='discipline',
#                 size_max=10,
#                 title=f"{selected_athlete} - Competition Results Over Time",
#                 hover_data=['event_name', 'location'] if 'event_name' in timeline_df.columns else None
#             )
#             # fig_timeline.update_yaxis(autorange="reversed")
#             fig_timeline.update_layout(height=500)
#             st.plotly_chart(fig_timeline, width='stretch')
    
#     # Performance by discipline
#     if len(athlete_df['discipline'].unique()) > 1:
#         st.subheader("Performance by Discipline")
        
#         discipline_stats = athlete_df.groupby('discipline').agg({
#             'round_rank': ['count', 'mean', 'min'] if 'round_rank' in athlete_df.columns else ['count'],
#             'year': ['min', 'max']
#         }).round(2)
        
#         discipline_stats.columns = ['_'.join(col).strip() for col in discipline_stats.columns.values]
#         discipline_stats = discipline_stats.reset_index()
        
#         st.dataframe(discipline_stats, width='stretch')
    
#     # ELO progression if available
#     if elo_df is not None:
#         athlete_elo = elo_df[
#             (elo_df['name'].str.lower() == selected_athlete.lower()) &
#             (elo_df['competed'] == True)
#         ].copy()
        
#         if not athlete_elo.empty:
#             st.subheader("ELO Rating Progression")
            
#             fig_elo = px.line(
#                 athlete_elo,
#                 x='date',
#                 y='elo_after',
#                 color='discipline',
#                 title=f"{selected_athlete} - ELO Rating History",
#                 markers=True
#             )
#             fig_elo.update_layout(height=400)
#             st.plotly_chart(fig_elo, width='stretch')

# def render_head_to_head(df, elo_df):
#     """Render head-to-head athlete comparison."""
    
#     st.subheader("Head-to-Head Comparison")

#     athletes = sorted([name.title() for name in df['name'].unique()])

#     col1, col2 = st.columns(2)
#     with col1:
#         default_athlete1 = "Ondra Adam" if "Ondra Adam" in athletes else athletes[0]
#         athlete1 = st.selectbox("Select First Athlete", athletes, index=athletes.index(default_athlete1) if default_athlete1 in athletes else 0, key="h2h_athlete1")
#     with col2:
#         default_athlete2 = "Schubert Jakob" if "Schubert Jakob" in athletes else (athletes[1] if len(athletes) > 1 else athletes[0])
#         athlete2 = st.selectbox("Select Second Athlete", athletes, index=athletes.index(default_athlete2) if default_athlete2 in athletes else (1 if len(athletes) > 1 else 0), key="h2h_athlete2")
    
#     if not athlete1 or not athlete2 or athlete1 == athlete2:
#         st.info("Please select two different athletes to compare")
#         return
    
#     # Get data for both athletes
#     athlete1_df = df[df['name'] == athlete1].copy()
#     athlete2_df = df[df['name'] == athlete2].copy()
    
#     # Comparison metrics
#     st.subheader("Comparison Overview")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.write(f"**{athlete1}**")
#         st.metric("Total Competitions", len(athlete1_df))
#         if 'round_rank' in athlete1_df.columns:
#             rank_data1 = athlete1_df.dropna(subset=['round_rank'])
#             if not rank_data1.empty:
#                 st.metric("Average Rank", f"{rank_data1['round_rank'].mean():.1f}")
#                 st.metric("Wins", (rank_data1['round_rank'] == 1).sum())
#                 st.metric("Podiums", (rank_data1['round_rank'] <= 3).sum())
    
#     with col2:
#         st.write(f"**{athlete2}**")
#         st.metric("Total Competitions", len(athlete2_df))
#         if 'round_rank' in athlete2_df.columns:
#             rank_data2 = athlete2_df.dropna(subset=['round_rank'])
#             if not rank_data2.empty:
#                 st.metric("Average Rank", f"{rank_data2['round_rank'].mean():.1f}")
#                 st.metric("Wins", (rank_data2['round_rank'] == 1).sum())
#                 st.metric("Podiums", (rank_data2['round_rank'] <= 3).sum())
    
#     # Direct matchups
#     st.subheader("Direct Matchups")
    
#     if 'event_name' in df.columns and 'round_rank' in df.columns:
#         # Find events where both competed
#         common_events = set(athlete1_df['event_name'].unique()) & set(athlete2_df['event_name'].unique())
        
#         if common_events:
#             matchups = []
#             for event in common_events:
#                 event_data1 = athlete1_df[athlete1_df['event_name'] == event]
#                 event_data2 = athlete2_df[athlete2_df['event_name'] == event]
                
#                 if not event_data1.empty and not event_data2.empty:
#                     rank1 = event_data1['round_rank'].iloc[0] if 'round_rank' in event_data1.columns else None
#                     rank2 = event_data2['round_rank'].iloc[0] if 'round_rank' in event_data2.columns else None
                    
#                     if pd.notna(rank1) and pd.notna(rank2):
#                         matchups.append({
#                             'Event': event,
#                             f'{athlete1} Rank': int(rank1),
#                             f'{athlete2} Rank': int(rank2),
#                             'Winner': athlete1 if rank1 < rank2 else athlete2 if rank2 < rank1 else 'Tie'
#                         })
            
#             if matchups:
#                 matchup_df = pd.DataFrame(matchups)
#                 st.dataframe(matchup_df, width='stretch')
                
#                 # Head-to-head record
#                 wins1 = (matchup_df['Winner'] == athlete1).sum()
#                 wins2 = (matchup_df['Winner'] == athlete2).sum()
#                 ties = (matchup_df['Winner'] == 'Tie').sum()
                
#                 st.write(f"**Head-to-Head Record**: {athlete1} {wins1} - {wins2} {athlete2} (Ties: {ties})")
#             else:
#                 st.info("No direct matchups found with ranking data")
#         else:
#             st.info("These athletes haven't competed in the same events")

# def render_location_performance(df):
#     """Render location-based performance analysis."""
    
#     st.subheader("Location Performance Analysis")
    
#     if 'location' not in df.columns:
#         st.warning("Location data not available")
#         return
    
#     location_df = df.dropna(subset=['location']).copy()
    
#     if location_df.empty:
#         st.warning("No location data found")
#         return
    
#     # Athlete selection
#     athletes = sorted(location_df['name'].unique())
#     default_athlete = "Ondra Adam" if "Ondra Adam" in athletes else athletes[0]
#     selected_athlete = st.selectbox("Select Athlete for Location Analysis", athletes, index=athletes.index(default_athlete) if default_athlete in athletes else 0,  key="location_athlete")
    
#     if not selected_athlete:
#         return
    
#     athlete_location_df = location_df[location_df['name'] == selected_athlete].copy()
    
#     if athlete_location_df.empty:
#         st.warning(f"No location data found for {selected_athlete}")
#         return
    
#     # Performance by location
#     if 'round_rank' in athlete_location_df.columns:
#         location_performance = athlete_location_df.groupby('location').agg({
#             'round_rank': ['mean', 'count', 'min'],
#             'year': ['min', 'max']
#         }).round(2)
        
#         location_performance.columns = ['avg_rank', 'competitions', 'best_rank', 'first_year', 'last_year']
#         location_performance = location_performance.reset_index()
#         location_performance = location_performance[location_performance['competitions'] >= 2]  # Filter for meaningful sample
        
#         if not location_performance.empty:
#             # Best and worst performing locations
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.subheader("Best Performing Locations")
#                 best_locations = location_performance.nsmallest(5, 'avg_rank')
                
#                 fig_best = px.bar(
#                     best_locations,
#                     x='avg_rank',
#                     y='location',
#                     orientation='h',
#                     title='Best Average Rankings by Location',
#                     labels={'avg_rank': 'Average Rank', 'location': 'Location'}
#                 )
#                 fig_best.update_layout(height=400, yaxis={'categoryorder':'total descending'})
#                 st.plotly_chart(fig_best, width='stretch')
            
#             with col2:
#                 st.subheader("Most Competed Locations")
#                 most_competed = location_performance.nlargest(5, 'competitions')
                
#                 fig_most = px.bar(
#                     most_competed,
#                     x='competitions',
#                     y='location',
#                     orientation='h',
#                     title='Most Competitions by Location',
#                     labels={'competitions': 'Number of Competitions', 'location': 'Location'}
#                 )
#                 fig_most.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
#                 st.plotly_chart(fig_most, width='stretch')
            
#             # Detailed location statistics
#             st.subheader("Detailed Location Statistics")
#             st.dataframe(location_performance.sort_values('avg_rank'), width='stretch')
     
#     # Global performance trends
#     st.subheader("Global Performance Trends")
    
#     # Overall location statistics
#     global_location_stats = location_df.groupby('location').agg({
#         'name': 'nunique',
#         'round_rank': 'mean' if 'round_rank' in location_df.columns else 'count',
#         'year': ['min', 'max']
#     }).round(2)
    
#     global_location_stats.columns = ['unique_athletes', 'avg_rank', 'first_event', 'last_event']
#     global_location_stats = global_location_stats.reset_index()
#     global_location_stats = global_location_stats[global_location_stats['unique_athletes'] >= 10]
    
#     if not global_location_stats.empty:
#         # Most competitive locations (by average rank)
#         competitive_locations = global_location_stats.nsmallest(10, 'avg_rank')
        
#         fig_competitive = px.scatter(
#             competitive_locations,
#             x='unique_athletes',
#             y='avg_rank',
#             size='unique_athletes',
#             hover_name='location',
#             title='Most Competitive Locations (Lower Avg Rank = More Competitive)',
#             labels={'unique_athletes': 'Number of Athletes', 'avg_rank': 'Average Rank'}
#         )
#         fig_competitive.update_layout(height=500)
#         st.plotly_chart(fig_competitive, width='stretch')
#######################################################################################
#######################################################################################

# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# from pathlib import Path
# import numpy as np

# def load_data():
#     """Load aggregated competition data."""
#     try:
#         data_file = Path("Data/aggregate_data/aggregated_results.csv")
#         if not data_file.exists():
#             return None
#         return pd.read_csv(data_file)
#     except Exception as e:
#         st.error(f"Error loading data: {e}")
#         return None

# def load_elo_data():
#     """Load ELO history data if available."""
#     try:
#         elo_file = Path("Elo_Data/elo_history.csv")
#         if elo_file.exists():
#             return pd.read_csv(elo_file, parse_dates=['date'])
#         return None
#     except Exception as e:
#         return None

# def render():
#     """Main render function for athlete analysis."""
#     st.header("Deep Dive Athlete Performance Analysis")
    
#     # Load data
#     df = load_data()
#     elo_df = load_elo_data()
    
#     if df is None or df.empty:
#         st.error("No competition data available")
#         return
    
#     # Clean and prepare data
#     df = prepare_data(df)
    
#     # Top section: Athlete selection with comparison option
#     render_athlete_selection(df, elo_df)

# def prepare_data(df):
#     """Clean and prepare the dataframe."""
#     df = df.dropna(subset=['name', 'year', 'discipline', 'gender'])
#     df['year'] = pd.to_numeric(df['year'], errors='coerce')
#     df = df.dropna(subset=['year'])
    
#     if 'start_date' in df.columns:
#         df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    
#     if 'round_rank' in df.columns:
#         df['round_rank'] = pd.to_numeric(df['round_rank'], errors='coerce')
    
#     return df

# def render_athlete_selection(df, elo_df):
#     """Render athlete selection and comparison setup."""
    
#     # Athlete selection section
#     st.subheader("Select Athletes for Analysis")
    
#     athletes = sorted(df['name'].unique())
    
#     col1, col2 = st.columns([2, 2])
    
#     with col1:
#         default_athlete1 = "Ondra Adam" if "Ondra Adam" in athletes else athletes[0]
#         primary_athlete = st.selectbox(
#             "Primary Athlete", 
#             athletes, 
#             index=athletes.index(default_athlete1) if default_athlete1 in athletes else 0,
#             key="primary_athlete"
#         )
    
#     with col2:
#         comparison_athletes = ["None"] + athletes
#         default_athlete2 = "None" #"Schubert Jakob" if "Schubert Jakob" in athletes else "None"
#         comparison_athlete = st.selectbox(
#             "Compare With (Optional)", 
#             comparison_athletes,
#             index=comparison_athletes.index(default_athlete2) if default_athlete2 in comparison_athletes else 0,
#             key="comparison_athlete"
#         )
    
#     comparison_mode = comparison_athlete != "None" and comparison_athlete != primary_athlete

#     # Filter data for selected athletes
#     primary_df = df[df['name'] == primary_athlete].copy()
#     comparison_df = df[df['name'] == comparison_athlete].copy() if comparison_mode else pd.DataFrame()
    
#     # Render all analysis sections
#     render_overview_metrics(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode, elo_df)
#     render_performance_timeline(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode)
#     render_discipline_breakdown(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode)
#     render_round_performance(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode)
#     render_location_analysis(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode)
#     render_peak_performance(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode)

# def render_overview_metrics(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode, elo_df):
#     """Render overview metrics section."""
#     st.subheader("Performance Overview")
    
#     if comparison_mode:
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.write(f"**{primary_athlete}**")
#             display_athlete_metrics(primary_df, elo_df, primary_athlete)
        
#         with col2:
#             st.write(f"**{comparison_athlete}**")
#             display_athlete_metrics(comparison_df, elo_df, comparison_athlete)
#     else:
#         st.write(f"**{primary_athlete}**")
#         display_athlete_metrics(primary_df, elo_df, primary_athlete)

# def display_athlete_metrics(athlete_df, elo_df, athlete_name):
#     """Display metrics for a single athlete."""
#     if athlete_df.empty:
#         st.warning("No data available")
#         return
    
#     col1, col2, col3, col4, col5, col6 = st.columns(6)

#     with col1:
#         total_comps = len(athlete_df)
#         st.metric("Total Competitions", total_comps)

#     with col2:
#         years_active = athlete_df['year'].max() - athlete_df['year'].min() + 1
#         st.metric("Years Active", years_active)

#     with col3:
#         avg_rank = None
#         if 'round_rank' in athlete_df.columns:
#             rank_data = athlete_df.dropna(subset=['round_rank'])
#             if not rank_data.empty:
#                 avg_rank = rank_data['round_rank'].mean()
#                 st.metric("Average Rank", f"{avg_rank:.1f}")

#     with col4:
#         if 'round_rank' in athlete_df.columns and not rank_data.empty:
#             wins = (rank_data['round_rank'] == 1).sum()
#             st.metric("Wins", wins)

#     with col5:
#         if 'round_rank' in athlete_df.columns and not rank_data.empty:
#             podiums = (rank_data['round_rank'] <= 3).sum()
#             st.metric("Podium Finishes", podiums)

#     with col6:
#         if elo_df is not None:
#             athlete_elo = elo_df[elo_df['name'] == athlete_name]
#             if not athlete_elo.empty:
#                 current_elo = athlete_elo['elo_after'].iloc[-1]
#                 st.metric("Current ELO", f"{current_elo:.0f}")


# def render_performance_timeline(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
#     """Render performance timeline analysis."""
#     st.subheader("Performance Timeline")
    
#     if 'start_date' not in primary_df.columns or 'round_rank' not in primary_df.columns:
#         st.warning("Timeline data not available")
#         return
    
#     fig = go.Figure()
    
#     # Primary athlete
#     timeline_primary = primary_df.dropna(subset=['start_date', 'round_rank']).sort_values('start_date')
#     if not timeline_primary.empty:
#         fig.add_trace(go.Scatter(
#             x=timeline_primary['start_date'],
#             y=timeline_primary['round_rank'],
#             mode='markers',
#             name=primary_athlete,
#             marker=dict(size=8),
#             line=dict(width=2)
#         ))
    
#     # Comparison athlete
#     if comparison_mode and not comparison_df.empty:
#         timeline_comparison = comparison_df.dropna(subset=['start_date', 'round_rank']).sort_values('start_date')
#         if not timeline_comparison.empty:
#             fig.add_trace(go.Scatter(
#                 x=timeline_comparison['start_date'],
#                 y=timeline_comparison['round_rank'],
#                 mode='markers',
#                 name=comparison_athlete,
#                 marker=dict(size=8),
#                 line=dict(width=2)
#             ))
    
#     fig.update_layout(
#         title="Competition Results Over Time",
#         xaxis_title="Date",
#         yaxis_title="Rank (Lower is Better)",
#         yaxis=dict(autorange="reversed"),
#         height=500
#     )
    
#     st.plotly_chart(fig, use_container_width=True)

# def render_discipline_breakdown(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
#     """Render discipline-specific performance breakdown."""
#     st.subheader("Performance by Discipline")
    
#     def get_discipline_stats(athlete_df):
#         if athlete_df.empty or 'round_rank' not in athlete_df.columns:
#             return pd.DataFrame()
        
#         return athlete_df.groupby('discipline').agg({
#             'round_rank': ['count', 'mean', 'min', lambda x: (x <= 3).sum(), lambda x: (x == 1).sum()],
#             'year': ['min', 'max']
#         }).round(2)
    
#     primary_stats = get_discipline_stats(primary_df)
    
#     if comparison_mode and not comparison_df.empty:
#         comparison_stats = get_discipline_stats(comparison_df)
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.write(f"**{primary_athlete}**")
#             if not primary_stats.empty:
#                 primary_stats.columns = ['Competitions', 'Avg Rank', 'Best Rank', 'Podiums', 'Wins', 'First Year', 'Last Year']
#                 st.dataframe(primary_stats, use_container_width=True)
        
#         with col2:
#             st.write(f"**{comparison_athlete}**")
#             if not comparison_stats.empty:
#                 comparison_stats.columns = ['Competitions', 'Avg Rank', 'Best Rank', 'Podiums', 'Wins', 'First Year', 'Last Year']
#                 st.dataframe(comparison_stats, use_container_width=True)
#     else:
#         if not primary_stats.empty:
#             primary_stats.columns = ['Competitions', 'Avg Rank', 'Best Rank', 'Podiums', 'Wins', 'First Year', 'Last Year']
#             st.dataframe(primary_stats, use_container_width=True)

# def render_round_performance(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
#     """Render performance by competition round."""
#     st.subheader("Performance by Competition Round")
    
#     if 'round' not in primary_df.columns or 'round_rank' not in primary_df.columns:
#         st.warning("Round data not available")
#         return
    
#     def get_round_stats(athlete_df):
#         if athlete_df.empty:
#             return pd.DataFrame()
        
#         round_data = athlete_df.dropna(subset=['round', 'round_rank'])
#         if round_data.empty:
#             return pd.DataFrame()
        
#         return round_data.groupby('round').agg({
#             'round_rank': ['count', 'mean', 'min', lambda x: (x <= 3).sum()]
#         }).round(2)
    
#     primary_round_stats = get_round_stats(primary_df)
    
#     if not primary_round_stats.empty:
#         primary_round_stats.columns = ['Competitions', 'Avg Rank', 'Best Rank', 'Podiums']
#         primary_round_stats = primary_round_stats.reset_index()
        
#         if comparison_mode and not comparison_df.empty:
#             comparison_round_stats = get_round_stats(comparison_df)
            
#             if not comparison_round_stats.empty:
#                 comparison_round_stats.columns = ['Competitions', 'Avg Rank', 'Best Rank', 'Podiums']
#                 comparison_round_stats = comparison_round_stats.reset_index()
                
#                 # Create comparison chart
#                 fig = make_subplots(rows=1, cols=2, subplot_titles=[primary_athlete, comparison_athlete])
                
#                 fig.add_trace(go.Bar(
#                     x=primary_round_stats['round'],
#                     y=primary_round_stats['Avg Rank'],
#                     name=primary_athlete,
#                     showlegend=False
#                 ), row=1, col=1)
                
#                 fig.add_trace(go.Bar(
#                     x=comparison_round_stats['round'],
#                     y=comparison_round_stats['Avg Rank'],
#                     name=comparison_athlete,
#                     showlegend=False
#                 ), row=1, col=2)
                
#                 fig.update_layout(title="Average Rank by Competition Round", height=400)
#                 fig.update_yaxes(autorange="reversed")
#                 st.plotly_chart(fig, use_container_width=True)
#         else:
#             # Single athlete chart
#             fig = px.bar(
#                 primary_round_stats,
#                 x='round',
#                 y='Avg Rank',
#                 title=f"{primary_athlete} - Average Rank by Round"
#             )
#             fig.update_yaxis(autorange="reversed")
#             st.plotly_chart(fig, use_container_width=True)
        
#         # Show detailed stats table
#         if comparison_mode and not comparison_df.empty:
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.write(f"**{primary_athlete} Round Statistics**")
#                 st.dataframe(primary_round_stats, use_container_width=True)
            
#             with col2:
#                 if not comparison_round_stats.empty:
#                     st.write(f"**{comparison_athlete} Round Statistics**")
#                     st.dataframe(comparison_round_stats, use_container_width=True)
#         else:
#             st.dataframe(primary_round_stats, use_container_width=True)

# def render_location_analysis(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
#     """Render location-based performance analysis."""
#     st.subheader("Performance by Location")
    
#     if 'location' not in primary_df.columns or 'round_rank' not in primary_df.columns:
#         st.warning("Location data not available")
#         return
    
#     def get_location_performance(athlete_df, min_competitions=2):
#         if athlete_df.empty:
#             return pd.DataFrame()
        
#         location_data = athlete_df.dropna(subset=['location', 'round_rank'])
#         if location_data.empty:
#             return pd.DataFrame()
        
#         stats = location_data.groupby('location').agg({
#             'round_rank': ['count', 'mean', 'min'],
#             'year': ['min', 'max']
#         }).round(2)
        
#         stats.columns = ['competitions', 'avg_rank', 'best_rank', 'first_year', 'last_year']
#         stats = stats.reset_index()
#         return stats[stats['competitions'] >= min_competitions]
    
#     primary_location_stats = get_location_performance(primary_df)
    
#     if comparison_mode and not comparison_df.empty:
#         comparison_location_stats = get_location_performance(comparison_df)
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.write(f"**{primary_athlete} - Best Locations**")
#             if not primary_location_stats.empty:
#                 best_primary = primary_location_stats.nsmallest(5, 'avg_rank')
#                 fig1 = px.bar(
#                     best_primary,
#                     x='avg_rank',
#                     y='location',
#                     orientation='h',
#                     title="Best Average Rankings"
#                 )
#                 fig1.update_layout(height=300, yaxis={'categoryorder':'total descending'})
#                 st.plotly_chart(fig1, use_container_width=True)
        
#         with col2:
#             st.write(f"**{comparison_athlete} - Best Locations**")
#             if not comparison_location_stats.empty:
#                 best_comparison = comparison_location_stats.nsmallest(5, 'avg_rank')
#                 fig2 = px.bar(
#                     best_comparison,
#                     x='avg_rank',
#                     y='location',
#                     orientation='h',
#                     title="Best Average Rankings"
#                 )
#                 fig2.update_layout(height=300, yaxis={'categoryorder':'total descending'})
#                 st.plotly_chart(fig2, use_container_width=True)
#     else:
#         if not primary_location_stats.empty:
#             best_locations = primary_location_stats.nsmallest(8, 'avg_rank')
            
#             fig = px.bar(
#                 best_locations,
#                 x='avg_rank',
#                 y='location',
#                 orientation='h',
#                 title=f"{primary_athlete} - Best Performing Locations",
#                 labels={'avg_rank': 'Average Rank', 'location': 'Location'}
#             )
#             fig.update_layout(height=400, yaxis={'categoryorder':'total descending'})
#             st.plotly_chart(fig, use_container_width=True)

# def render_peak_performance(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
#     """Render peak performance identification."""
#     st.subheader("Peak Performance Analysis")
    
#     if 'year' not in primary_df.columns or 'round_rank' not in primary_df.columns:
#         st.warning("Year and rank data required for peak analysis")
#         return
    
#     def get_yearly_performance(athlete_df):
#         if athlete_df.empty:
#             return pd.DataFrame()
        
#         yearly_data = athlete_df.dropna(subset=['year', 'round_rank'])
#         if yearly_data.empty:
#             return pd.DataFrame()
        
#         return yearly_data.groupby('year').agg({
#             'round_rank': ['count', 'mean', 'min'],
#             'name': 'count'
#         }).round(2)
    
#     primary_yearly = get_yearly_performance(primary_df)
    
#     if not primary_yearly.empty:
#         primary_yearly.columns = ['competitions', 'avg_rank', 'best_rank', 'total_entries']
#         primary_yearly = primary_yearly.reset_index()
        
#         # Yearly performance chart
#         if comparison_mode and not comparison_df.empty:
#             comparison_yearly = get_yearly_performance(comparison_df)
#             if not comparison_yearly.empty:
#                 comparison_yearly.columns = ['competitions', 'avg_rank', 'best_rank', 'total_entries']
#                 comparison_yearly = comparison_yearly.reset_index()
                
#                 fig = go.Figure()
                
#                 fig.add_trace(go.Scatter(
#                     x=primary_yearly['year'],
#                     y=primary_yearly['avg_rank'],
#                     mode='lines+markers',
#                     name=primary_athlete,
#                     line=dict(width=3)
#                 ))
                
#                 fig.add_trace(go.Scatter(
#                     x=comparison_yearly['year'],
#                     y=comparison_yearly['avg_rank'],
#                     mode='lines+markers',
#                     name=comparison_athlete,
#                     line=dict(width=3)
#                 ))
                
#                 fig.update_layout(
#                     title="Average Performance by Year",
#                     xaxis_title="Year",
#                     yaxis_title="Average Rank (Lower is Better)",
#                     yaxis=dict(autorange="reversed"),
#                     height=400
#                 )
                
#                 st.plotly_chart(fig, use_container_width=True)
#         else:
#             fig = px.line(
#                 primary_yearly,
#                 x='year',
#                 y='avg_rank',
#                 title=f"{primary_athlete} - Performance Evolution",
#                 markers=True
#             )
#             fig.update_yaxis(autorange="reversed")
#             fig.update_layout(height=400)
#             st.plotly_chart(fig, use_container_width=True)

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
    """Main render function for athlete analysis."""
    st.header("Deep Dive Athlete Performance Analysis")
    
    # Load data
    df = load_data()
    elo_df = load_elo_data()
    
    if df is None or df.empty:
        st.error("No competition data available")
        return
    
    # Clean and prepare data
    df = prepare_data(df)
    
    # Top section: Athlete selection with comparison option
    render_athlete_selection(df, elo_df)

def prepare_data(df):
    """Clean and prepare the dataframe."""
    df = df.dropna(subset=['name', 'year', 'discipline', 'gender'])
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df = df.dropna(subset=['year'])
    
    if 'start_date' in df.columns:
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    
    if 'round_rank' in df.columns:
        df['round_rank'] = pd.to_numeric(df['round_rank'], errors='coerce')
    
    return df

def render_athlete_selection(df, elo_df):
    """Render athlete selection and comparison setup."""
    
    # Athlete selection section
    st.subheader("Select Athletes for Analysis")
    
    athletes = sorted(df['name'].unique())
    
    col1, col2 = st.columns([2, 2])
    
    with col1:
        default_athlete1 = "Ondra Adam" if "Ondra Adam" in athletes else athletes[0]
        st.markdown("<span style='color: #1f77b4;'>Primary Athlete</span>", unsafe_allow_html=True)
        primary_athlete = st.selectbox(
            "Primary Athlete", 
            athletes, 
            index=athletes.index(default_athlete1) if default_athlete1 in athletes else 0,
            key="primary_athlete",
            label_visibility="collapsed"
        )

    with col2:
        comparison_athletes = ["None"] + athletes
        default_athlete2 = "Schubert Jakob" if "Schubert Jakob" in athletes else "None" #"None"
        st.markdown("<span style='color: #ff7f0e;'>Compare With (Optional)</span>", unsafe_allow_html=True)
        comparison_athlete = st.selectbox(
            "Compare With (Optional)", 
            comparison_athletes,
            index=comparison_athletes.index(default_athlete2) if default_athlete2 in comparison_athletes else 0,
            key="comparison_athlete",
            label_visibility="collapsed"
        )
    
    comparison_mode = comparison_athlete != "None" and comparison_athlete != primary_athlete

    # Filter data for selected athletes
    primary_df = df[df['name'] == primary_athlete].copy()
    comparison_df = df[df['name'] == comparison_athlete].copy() if comparison_mode else pd.DataFrame()
    
    # Render all analysis sections
    render_overview_metrics(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode, elo_df)
    render_elo_history(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode, elo_df)
    render_performance_timeline(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode)
    render_discipline_round_analysis(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode)
    render_location_analysis(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode)

def render_overview_metrics(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode, elo_df):
    """Render overview metrics section."""
    st.subheader("Performance Overview")
    
    # Primary athlete (always shown)
    st.markdown(f"<h4 style='color: #1f77b4;'>{primary_athlete}</h4>", unsafe_allow_html=True)
    display_athlete_metrics(primary_df, elo_df, primary_athlete)
    
    # Comparison athlete (vertically stacked)
    if comparison_mode:
        st.markdown(f"<h4 style='color: #ff7f0e;'>{comparison_athlete}</h4>", unsafe_allow_html=True)
        display_athlete_metrics(comparison_df, elo_df, comparison_athlete)

def display_athlete_metrics(athlete_df, elo_df, athlete_name):
    """Display metrics for a single athlete."""
    if athlete_df.empty:
        st.warning("No data available")
        return
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        total_comps = len(athlete_df)
        st.metric("Total Competitions", total_comps)

    with col2:
        years_active = athlete_df['year'].max() - athlete_df['year'].min() + 1
        st.metric("Years Active", years_active)

    rank_data = athlete_df.dropna(subset=['round_rank']) if 'round_rank' in athlete_df.columns else pd.DataFrame()
    
    with col3:
        if not rank_data.empty:
            avg_rank = rank_data['round_rank'].mean()
            st.metric("Average Rank", f"{avg_rank:.1f}")

    with col4:
        if not rank_data.empty:
            wins = (rank_data['round_rank'] == 1).sum()
            st.metric("Wins", wins)

    with col5:
        if not rank_data.empty:
            podiums = (rank_data['round_rank'] <= 3).sum()
            st.metric("Podium Finishes", podiums)

    with col6:
        if elo_df is not None:
            athlete_elo = elo_df[elo_df['name'] == athlete_name]
            if not athlete_elo.empty:
                current_elo = athlete_elo['elo_after'].iloc[-1]
                st.metric("Current ELO", f"{current_elo:.0f}")

def render_elo_history(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode, elo_df):
    """Render ELO rating history."""
    if elo_df is None:
        return
    
    st.subheader("ELO Rating History")
    
    fig = go.Figure()
    
    # Primary athlete ELO
    primary_elo = elo_df[(elo_df['name'] == primary_athlete) & (elo_df['competed'] == True)]
    if not primary_elo.empty:
        fig.add_trace(go.Scatter(
            x=primary_elo['date'],
            y=primary_elo['elo_after'],
            mode='lines+markers',
            name=primary_athlete,
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6)
        ))
    
    # Comparison athlete ELO
    if comparison_mode and not comparison_df.empty:
        comparison_elo = elo_df[(elo_df['name'] == comparison_athlete) & (elo_df['competed'] == True)]
        if not comparison_elo.empty:
            fig.add_trace(go.Scatter(
                x=comparison_elo['date'],
                y=comparison_elo['elo_after'],
                mode='lines+markers',
                name=comparison_athlete,
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=6)
            ))
    
    fig.update_layout(
        title="ELO Rating Progression",
        xaxis_title="Date",
        yaxis_title="ELO Rating",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_performance_timeline(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
    """Render performance timeline analysis."""
    st.subheader("Performance Timeline")
    
    if 'start_date' not in primary_df.columns or 'round_rank' not in primary_df.columns:
        st.warning("Timeline data not available")
        return
    
    fig = go.Figure()
    
    # Primary athlete
    timeline_primary = primary_df.dropna(subset=['start_date', 'round_rank']).sort_values('start_date')
    if not timeline_primary.empty:
        fig.add_trace(go.Scatter(
            x=timeline_primary['start_date'],
            y=timeline_primary['round_rank'],
            mode='markers',
            name=primary_athlete,
            marker=dict(size=8, color='#1f77b4')
        ))
    
    # Comparison athlete
    if comparison_mode and not comparison_df.empty:
        timeline_comparison = comparison_df.dropna(subset=['start_date', 'round_rank']).sort_values('start_date')
        if not timeline_comparison.empty:
            fig.add_trace(go.Scatter(
                x=timeline_comparison['start_date'],
                y=timeline_comparison['round_rank'],
                mode='markers',
                name=comparison_athlete,
                marker=dict(size=8, color='#ff7f0e')
            ))
    
    fig.update_layout(
        title="Competition Results Over Time",
        xaxis_title="Date",
        yaxis_title="Rank (Lower is Better)",
        yaxis=dict(autorange="reversed"),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_discipline_round_analysis(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
    """Render combined discipline and round performance analysis with funnel charts."""
    st.subheader("Performance by Discipline & Round")
    
    # Only show Boulder and Lead disciplines
    disciplines_to_show = ['Boulder', 'Lead']
    
    # Get available disciplines for each athlete
    primary_disciplines = set(primary_df['discipline'].unique()) if not primary_df.empty else set()
    comparison_disciplines = set(comparison_df['discipline'].unique()) if comparison_mode and not comparison_df.empty else set()
    
    if comparison_mode:
        available_disciplines = primary_disciplines.union(comparison_disciplines)
    else:
        available_disciplines = primary_disciplines
    
    # Filter to only Boulder and Lead
    disciplines_to_display = [d for d in disciplines_to_show if d in available_disciplines]
    
    if not disciplines_to_display:
        st.warning("No Boulder or Lead discipline data available")
        return
    
    # Create funnel chart for each discipline
    for discipline in disciplines_to_display:
        # Prepare funnel data
        funnel_data = []
        round_order = ['Qualification', 'Semi-Final', 'Final']
        
        # Primary athlete data
        primary_disc_data = primary_df[primary_df['discipline'] == discipline]
        for round_name in round_order:
            round_data = primary_disc_data[primary_disc_data['round'] == round_name]
            if not round_data.empty and 'round_rank' in round_data.columns:
                rank_data = round_data.dropna(subset=['round_rank'])
                if not rank_data.empty:
                    funnel_data.append({
                        'competitions': len(rank_data),
                        'round': round_name,
                        'athlete': primary_athlete,
                        'avg_rank': rank_data['round_rank'].mean()
                    })
        
        # Comparison athlete data
        if comparison_mode:
            comparison_disc_data = comparison_df[comparison_df['discipline'] == discipline]
            for round_name in round_order:
                round_data = comparison_disc_data[comparison_disc_data['round'] == round_name]
                if not round_data.empty and 'round_rank' in round_data.columns:
                    rank_data = round_data.dropna(subset=['round_rank'])
                    if not rank_data.empty:
                        funnel_data.append({
                            'competitions': len(rank_data),
                            'round': round_name,
                            'athlete': comparison_athlete,
                            'avg_rank': rank_data['round_rank'].mean()
                        })
        
        if funnel_data:
            funnel_df = pd.DataFrame(funnel_data)
            
            # Create funnel chart
            fig = px.funnel(
                funnel_df, 
                x='competitions', 
                y='round', 
                color='athlete',
                title=f"{discipline} - Competition Progression",
                color_discrete_map={primary_athlete: '#1f77b4', comparison_athlete: '#ff7f0e'} if comparison_mode else {primary_athlete: '#1f77b4'},
                text='competitions'
            )

            # Remove 3D effects by updating layout
            fig.update_layout(height=400)

            # Make funnel bars flat (remove any 3D styling)
            fig.update_traces(textinfo='text', textposition='inside', textfont_size=16)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No round data available for {discipline}")

def render_location_analysis(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
    """Render location-based performance analysis with world map."""
    st.subheader("Performance by Location")
    
    if 'location' not in primary_df.columns or 'round_rank' not in primary_df.columns:
        st.warning("Location data not available")
        return
    
    # Location to country mapping
    location_to_country = {
        'Germany': ['Frankfurt', 'Nürnberg', 'München', 'Munich', 'Leipzig', 'Erlangen', 'Dresden'],
        'India': ['NaviMumbai', 'Mumbai'],
        'Jordan': ['Amman'],
        'Canada': ['Laval', 'Canmore', 'Toronto', 'Saanich'],
        'Switzerland': ['Zürich', 'Genève', 'Winterthur', 'Bern', 'Grindelwald', 'Meiringen', 'Villars', 'Villars-sur-Ollon', 'Bern, SUI', 'Greifensee'],
        'Slovenia': ['Kranj', 'Ljubljana', 'Log-Dragomer', 'Koper', 'Koper, SLO'],
        'Singapore': ['Singapore'],
        'Bulgaria': ['Black See', 'Veliko Tarnovo', 'Sofia'],
        'Russia': ['Moscow', 'Ekaterinburg', 'Yekaterinburg', 'Perm'],
        'Brazil': ['Curitiba, BRA'],
        'Austria': ['Wien', 'Vienna', 'Innsbruck', 'St. Pölten', 'Graz', 'Wiener Neustadt', 'Hall', 'Kitzbühel', 'Innsbruck, AUT', 'Brixen', 'Imst', 'Villach', 'Tyrol'],
        'Japan': ['Tokio', 'Tokyo', 'Kobe', 'Kazo', 'Inzai', 'Hachioji', 'Japan'],
        'Indonesia': ['Jakarta', 'Indonesia', 'Bali, INA'],
        'Poland': ['Tarnow', 'Krakow, POL'],
        'Malaysia': ['Kuala Lumpur'],
        'United States': ['Vail', 'Boulder', 'Atlanta', 'Salt Lake City', 'Salt Lake CIty', 'Salt Lake City, USA', 'Denver, USA'],
        'Spain': ['Benasque', 'Aviles', 'Marbella', 'Barcelona', 'Gijon', 'Madrid, ESP'],
        'Greece': ['Konitsa'],
        'Italy': ['Clusone', 'Milan', 'Milano', 'Courmayeur', 'Bardonecchia', 'Cortina', 'Rovereto', 'Lecco', 'Bolzano', 'Fiera di Primiero', 'Val Daone', 'Daone', 'Trento', 'Aprica', 'Arco', 'Arco Group A', 'Arco Group B'],
        'Czech Republic': ['Prag', 'Prague', 'Brno', 'Prague, CZE'],
        'Azerbaijan': ['Baku'],
        'United Kingdom': ['Birmingham', 'Edinburgh', 'Sheffield'],
        'China': ['Shenzen', 'Shanghai', 'Huzou', 'Qinghai Province', 'Qinghai', 'Qinghai m', 'Quinghai', 'Xining', 'Huaiji', 'Changzhi', 'Chongqing', 'Haiyang', 'Wujiang', 'Nanjing', 'Xiamen', 'Taian', 'Keqiao', 'Keqiao, CHN', 'Wujiang, CHN', 'Guiyang, CHN'],
        'Norway': ['Stavanger'],
        'South Korea': ['Chuncheon', 'Mokpo', 'Seoul'],
        'France': ['Toulon', 'Aix-les-Bains', 'Besancon', "Val d'Isere", 'Chamonix', 'Grenoble', 'Millau', 'Nantes', 'GAP', "L'Argentière", "L'Argentière La Bessée", 'Valence', 'Firminy', 'Penne', 'Montauban', 'Briançon', 'Briancon', 'Chamonix, FRA', 'Beauregard', 'Paris', 'La Reunion', 'Reunion'],
        'Netherlands': ['Eindhoven'],
        'Belgium': ['Puurs'],
    }

    
    def get_location_performance(athlete_df, min_competitions=2):
        if athlete_df.empty:
            return pd.DataFrame()
        
        location_data = athlete_df.dropna(subset=['location', 'round_rank'])
        if location_data.empty:
            return pd.DataFrame()
        
        stats = location_data.groupby('location').agg({
            'round_rank': ['count', 'mean', 'min']
        }).round(2)
        
        stats.columns = ['competitions', 'avg_rank', 'best_rank']
        stats = stats.reset_index()
        filtered_stats = stats[stats['competitions'] >= min_competitions]
        
        # Add country mapping
        location_to_country_map = {loc: country for country, locs in location_to_country.items() for loc in locs}
        filtered_stats['country'] = filtered_stats['location'].map(location_to_country_map)
        filtered_stats = filtered_stats.dropna(subset=['country'])

        return filtered_stats
    
    primary_location_stats = get_location_performance(primary_df)
    
    if comparison_mode and not comparison_df.empty:
        comparison_location_stats = get_location_performance(comparison_df)

        # Merge primary and comparison stats by country
        merged_stats = pd.merge(
            primary_location_stats[['country', 'avg_rank']].rename(columns={'avg_rank': f'avg_rank_{primary_athlete}'}),
            comparison_location_stats[['country', 'avg_rank']].rename(columns={'avg_rank': f'avg_rank_{comparison_athlete}'}),
            on='country',
            how='outer'
        )

        # Ensure one row per country
        merged_stats = merged_stats.groupby('country').agg({
            f'avg_rank_{primary_athlete}': 'mean',  # avg if multiple entries
            f'avg_rank_{comparison_athlete}': 'mean'
        }).reset_index()

        # Determine who is better
        merged_stats['best_athlete'] = merged_stats.apply(
            lambda row: primary_athlete if row[f'avg_rank_{primary_athlete}'] <= row[f'avg_rank_{comparison_athlete}'] else comparison_athlete,
            axis=1
        )

        merged_stats['best_avg_rank'] = merged_stats[[f'avg_rank_{primary_athlete}', f'avg_rank_{comparison_athlete}']].min(axis=1)
        merged_stats['hover_label'] = merged_stats['best_athlete'] + " dominates"


        # Plot choropleth
        fig = px.choropleth(
            merged_stats,
            locations='country',
            locationmode='country names',
            color='best_avg_rank',
            hover_name='hover_label',
            hover_data=[f'avg_rank_{primary_athlete}', f'avg_rank_{comparison_athlete}', 'country'],
            color_continuous_scale='Sunset',
            range_color=[np.nanmax(merged_stats['best_avg_rank']), np.nanmin(merged_stats['best_avg_rank'])],
            title=f"{primary_athlete} vs {comparison_athlete} - Best Athlete by Country",
        )

        fig.update_layout(
            height=600,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="#1e1e1e",
            plot_bgcolor="#1e1e1e",
        )

        fig.update_traces(
            marker_line_color='black',  # optional: add borders to countries
            selector=dict(type='choropleth')
        )
        fig.update_geos(
            projection_type="natural earth",
            # lataxis_range=[-10, 80],
            bgcolor="rgba(30,30,30,1)",  # dark background
            showcoastlines=True,
            coastlinecolor="gray",
            showland=True,
            landcolor="rgba(50,50,50,1)",  # countries with no data
            showocean=True,
            oceancolor="#111111"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        # Single athlete
        if not primary_location_stats.empty:
            primary_location_stats['best_athlete'] = primary_athlete
            primary_location_stats['best_avg_rank'] = primary_location_stats['avg_rank']

            min_rank = primary_location_stats['best_avg_rank'].min()
            max_rank = primary_location_stats['best_avg_rank'].max()

            fig = px.choropleth(
                primary_location_stats,
                locations='country',
                locationmode='country names',
                color='best_avg_rank',
                hover_name='best_athlete',
                hover_data=['best_avg_rank', 'country'],
                color_continuous_scale='RdYlGn_r',
                range_color=[min_rank, max_rank],
                title=f"{primary_athlete} - Performance by Country",
                labels={'best_avg_rank': 'Average Rank'}
            )

            fig.update_layout(
                height=600,
                margin=dict(l=20, r=20, t=50, b=20),
                paper_bgcolor="#1e1e1e",
                plot_bgcolor="#1e1e1e",
            )

            st.plotly_chart(fig, use_container_width=True)