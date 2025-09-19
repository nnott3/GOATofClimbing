import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

def render(analyzer, calculator, filters):
    """Render the ELO Rankings tab with improved error handling and performance."""
    
    # Load ELO data with error handling
    elo_file = Path("Elo_Data/elo_history.csv")
    
    if not elo_file.exists():
        st.error("ELO data not found. Please run ELO calculations first.")
        if st.button("Calculate ELO Ratings"):
            with st.spinner("Calculating ELO ratings..."):
                try:
                    calculator.calculate_elo_ratings()
                    calculator.save_results()
                    st.success("ELO ratings calculated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error calculating ELO: {e}")
        return
    
    try:
        elo_df = pd.read_csv(elo_file, parse_dates=['date'])
    except Exception as e:
        st.error(f"Error loading ELO data: {e}")
        return

    if elo_df.empty:
        st.warning("No ELO data available.")
        return

    # Clean data
    elo_df = elo_df.dropna(subset=['name', 'discipline', 'gender'])
    elo_df = elo_df[~elo_df['name'].isin(['none', 'na', 'None', 'NA', ''])]

    col_left, col_right = st.columns([1, 3])
    
    with col_left:
        st.subheader("Filters")

        # Get available options from data
        available_disciplines = sorted(elo_df['discipline'].unique())
        available_genders = sorted(elo_df['gender'].unique())

        if not available_disciplines or not available_genders:
            st.error("No valid discipline or gender data found.")
            return
        
        # Era definitions
        DISCIPLINE_ERAS = {
            "Lead": [
                ("IFSC Modern", "2007-01-01", "2025-12-31"),
                ("UIAA Legacy", "1991-01-01", "2006-12-31"),
            ],
            "Boulder": [
                ("IFSC Current", "2025-01-01", "2025-12-31"),
                ("IFSC Zone/Top", "2007-01-01", "2024-12-31"),
                ("UIAA Legacy", "1991-01-01", "2006-12-31"),
            ],
            "Speed": [
                ("IFSC Time", "2009-01-01", "2025-12-31"),
                ("IFSC Score", "2007-01-01", "2008-12-31"),
                ("UIAA Legacy", "1991-01-01", "2006-12-31"),
            ]
        }
        
        # Discipline selection
        st.write("**Discipline:**")
        discipline = st.pills(
            "Discipline",
            options=available_disciplines,
            default="Boulder" if "Boulder" in available_disciplines else available_disciplines[0],
            label_visibility="collapsed"
        )
        
        # Gender selection
        st.write("**Gender:**")
        gender = st.pills(
            "Gender", 
            options=available_genders,
            default="Women" if "Women" in available_genders else available_genders[0],
            label_visibility="collapsed"
        )

        # Get date range from actual data
        min_date = elo_df['date'].min()
        max_date = elo_df['date'].max()
        default_eras = [("All Time", min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d'))]
        
        eras = DISCIPLINE_ERAS.get(discipline, default_eras)
        era_options = [f"{label} ({start[:4]}-{end[:4]})" for label, start, end in eras]
        
        st.write("**Era:**")
        selected_era = st.pills("Era", options=era_options, 
                                default=era_options[1] if discipline == "Boulder" else era_options[0],
                                label_visibility="collapsed")
        era_idx = era_options.index(selected_era)
        era_label, era_start, era_end = eras[era_idx]
        # Filter data
        era_start_date = pd.to_datetime(era_start)
        era_end_date = pd.to_datetime(era_end)
        
        filtered_df = elo_df[
            (elo_df["date"] >= era_start_date) &
            (elo_df["date"] <= era_end_date) &
            (elo_df["discipline"] == discipline) &
            (elo_df["gender"] == gender) &
            (elo_df["competed"] == True)  # Only actual competitions
        ]

        if filtered_df.empty:
            st.warning(f"No data found for {discipline} {gender} in {era_label} era.")
            return

        # Generate leaderboard
        leaderboard = (
            filtered_df.sort_values(['name', 'date'])
            .groupby('name')
            .last()[['elo_after']]
            .sort_values('elo_after', ascending=False)
            .head(10)
            .reset_index()
        )
        
        leaderboard['rank'] = range(1, len(leaderboard) + 1)
        leaderboard['elo_after'] = leaderboard['elo_after'].round(0).astype(int)
        
        st.subheader("Current Rankings")
        st.dataframe(
            leaderboard[['rank', 'name', 'elo_after']].rename(columns={
                'rank': 'Rank',
                'name': 'Athlete', 
                'elo_after': 'ELO'
            }),
            hide_index=True,
            width='stretch'
        )
    
    with col_right:
        if leaderboard.empty:
            st.warning("No athletes found for selected criteria.")
            return
        
        # Athlete selection for plotting
        default_athletes = leaderboard["name"].head(6).tolist()
        selected_athletes = st.multiselect(
            "Select Athletes to Track",
            options=leaderboard["name"].tolist(),
            default=default_athletes,
            help="Choose athletes to display on the ELO history chart",
            key="elo_athletes"
        )
        
        if not selected_athletes:
            st.info("Please select at least one athlete to view ELO history.")
            return
        
        # Prepare plot data
        plot_data = filtered_df[
            filtered_df['name'].isin(selected_athletes)
        ].sort_values(['name', 'date'])
        
        if plot_data.empty:
            st.warning("No data available for selected athletes in this time period.")
            return
        
        # Create ELO history plot
        fig = px.line(
            plot_data,
            x="date",
            y="elo_after",
            color="name",
            markers=True,
            title=f"ELO History - {discipline} {gender} ({era_label})",
            hover_data={
                'date': '|%B %d, %Y',
                'elo_after': ':.0f',
                'event': True,
                'rank': True,
                'name': False
            }
        )
        
        # Improve plot appearance
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="ELO Rating",
            legend_title="Athlete",
            template="plotly_white",
            height=600,
            hovermode='x unified'
        )
        
        fig.update_traces(
            mode='lines+markers',
            marker_size=6,
            line_width=2
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Summary statistics
        if len(selected_athletes) > 0:
            st.subheader("Summary Statistics")
            
            # Calculate stats for selected athletes
            stats_data = []
            for athlete in selected_athletes:
                athlete_data = plot_data[plot_data['name'] == athlete]
                if not athlete_data.empty:
                    stats_data.append({
                        'Athlete': athlete,
                        'Current ELO': int(athlete_data['elo_after'].iloc[-1]),
                        'Peak ELO': int(athlete_data['elo_after'].max()),
                        'Competitions': len(athlete_data),
                        'Avg Rank': athlete_data['rank'].mean().round(1),
                        'Wins': (athlete_data['rank'] == 1).sum(),
                        'Podiums': (athlete_data['rank'] <= 3).sum()
                    })
            
            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, hide_index=True, width='stretch')