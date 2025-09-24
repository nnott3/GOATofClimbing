import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import numpy as np
import re

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
    """Render the event analysis dashboard."""
    st.header("Competition Event Analysis")
    
    # Load data
    df = load_data()
    if df is None or df.empty:
        st.error("No competition data available")
        return
    
    # Clean and prepare data
    df = prepare_data(df)
    
    # Filters section
    render_filters(df)

def prepare_data(df):
    """Clean and prepare the dataframe."""
    df = df.dropna(subset=['event_name', 'year', 'discipline', 'gender'])
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df = df.dropna(subset=['year'])
    
    if 'round_rank' in df.columns:
        df['round_rank'] = pd.to_numeric(df['round_rank'], errors='coerce')
    
    return df

def render_filters(df):
    """Render filter controls and display results."""
    
    # Filter controls
    col1, col2, col3, col4 = st.columns([1,1,2,2])
    
    with col1:
        st.write("**Gender:**")
        genders = sorted(df['gender'].unique())
        selected_gender = st.pills("Gender", options=genders, default=genders[0], label_visibility="collapsed")
    
    with col2:
        st.write("**Discipline:**")
        disciplines = ['Boulder', 'Lead']  # Skip Speed for now
        available_disciplines = [d for d in disciplines if d in df['discipline'].unique()]
        selected_discipline = st.pills("Discipline", options=available_disciplines, 
                                     default="Lead" if available_disciplines else available_disciplines[0], 
                                     label_visibility="collapsed")
    
    with col3:
        st.write("**Year:**")
        min_year = int(df['year'].min())
        max_year = int(df['year'].max())
        selected_year = st.slider("Year", min_value=min_year, max_value=max_year, 
                                value=max_year, label_visibility="collapsed")
    
    # Filter data based on selections
    filtered_df = df[
        (df['gender'] == selected_gender) &
        (df['discipline'] == selected_discipline) &
        (df['year'] == selected_year)
    ]
    
    if filtered_df.empty:
        st.warning("No events found for selected filters")
        return
    
    with col4:
        st.write("**Event:**")
        events = sorted(filtered_df['location'].unique())
        selected_event = st.pills("Event", options=events, default=events[0], label_visibility="collapsed")
    
    # Filter to selected event
    event_df = filtered_df[filtered_df['location'] == selected_event]
    
    if event_df.empty:
        st.warning("No data found for selected event")
        return
    
    # Display event results based on discipline
    if selected_discipline == 'Boulder':
        render_boulder_event(event_df, selected_event)
    elif selected_discipline == 'Lead':
        render_lead_event(event_df, selected_event)

def calculate_boulder_score(row):
    """Calculate boulder score if not already present."""
    if pd.notna(row.get('boulder_score')):
        return row['boulder_score']
    
    total_score = 0
    for i in range(1, 6):  # P1 to P5
        top_col = f'p{i}_top'
        zone_col = f'p{i}_zone'
        
        if top_col in row and zone_col in row:
            top_val = row[top_col]
            zone_val = row[zone_col]
            
            # Skip if no data
            if pd.isna(top_val) or pd.isna(zone_val) or top_val == 'X':
                continue
            
            try:
                # Top = 25 points, Zone = 10 points, attempts cost -0.1 each
                if top_val != 'X':
                    top_attempts = float(top_val)
                    total_score += 25 - (top_attempts * 0.1)
                elif zone_val != 'X':
                    zone_attempts = float(zone_val)
                    total_score += 10 - (zone_attempts * 0.1)
            except (ValueError, TypeError):
                continue
    
    return total_score
        

def render_boulder_event(event_df, event_name):
    """Render boulder event analysis with wide graph + metrics layout."""
    st.subheader(f"🧗 Boulder: {event_df[event_df['location'] == event_name]['event_name'].iloc[0]}")
    
    event_df['calculated_score'] = event_df.apply(calculate_boulder_score, axis=1)
    
    rounds = ['Qualification', 'Semi-Final', 'Final']
    available_rounds = [r for r in rounds if r in event_df['round'].unique()]
    
    if not available_rounds:
        st.warning("No round data available")
        return
    
    for round_name in available_rounds:
        st.write(f"### {round_name}")
        round_df = event_df[event_df['round'] == round_name].copy()
        if round_df.empty:
            continue
        
        # Analyze problems
        problems_data = []
        for i in range(1, 6):  # P1 to P5
            top_col, zone_col = f'p{i}_top', f'p{i}_zone'
            if top_col not in round_df.columns or zone_col not in round_df.columns:
                continue
            valid_attempts = round_df[(round_df[top_col].notna()) & (round_df[zone_col].notna())]
            if valid_attempts.empty:
                continue
            
            tops = len(valid_attempts[valid_attempts[top_col] != 'X'])
            zones_only = len(valid_attempts[(valid_attempts[top_col] == 'X') & (valid_attempts[zone_col] != 'X')])
            no_progress = len(valid_attempts[(valid_attempts[top_col] == 'X') & (valid_attempts[zone_col] == 'X')])
            total = len(valid_attempts)
            
            problems_data.append({
                'problem': f'P{i}',
                'tops': tops,
                'zones_only': zones_only,
                'no_progress': no_progress,
                'total': total,
                'top_rate': tops / total * 100
            })
        
        if not problems_data:
            continue
        
        problems_df = pd.DataFrame(problems_data)
        
        # Layout: wide graph left, metrics right
        col_graph, col0, col_metrics = st.columns([5, 1, 1])
        
        with col_graph:
            fig = go.Figure()
            colors = ['#1E8449', '#FF9900', '#444444']  # green, orange, dark_grey
            names = ['Tops', 'Zones Only', 'No Progress']
            data_cols = ['tops', 'zones_only', 'no_progress']        
            
            for name, col, color in zip(names, data_cols, colors):
                if col == 'tops':
                    text = [f"{val} ({rate:.0f}%)" for val, rate in zip(problems_df[col], problems_df['top_rate'])]
                elif col == 'zones_only':
                    zone_rates = problems_df['zones_only']/problems_df['total']*100
                    text = [f"{val} ({rate:.0f}%)" for val, rate in zip(problems_df[col], zone_rates)]
                else:
                    text = problems_df[col]
                
                fig.add_trace(go.Bar(
                    name=name,
                    x=problems_df[col],
                    y=problems_df['problem'],
                    orientation='h', 
                    marker_color=color,
                    text=text,
                    textposition='inside',
                    textfont=dict(color='white', size=12, family='Arial Black')
                ))
            
            fig.update_layout(
                xaxis_title="<b>Athletes</b>",
                yaxis_title="<b>Problem</b>",
                barmode='stack',
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig)
        
        with col_metrics:
            st.metric("Athletes", int(problems_df['total'].max()))
            st.metric("Avg Tops", f"{problems_df['tops'].mean():.1f}")
            hardest = problems_df.loc[problems_df['top_rate'].idxmin(), 'problem']
            st.metric("Hardest", hardest)

            
def parse_lead_score(score_str):
    """Parse lead score string into numeric value with jittering."""
    if pd.isna(score_str):
        return None
    
    score_str = str(score_str).strip()
    
    # Handle "Top" case
    if score_str.lower() == 'top':
        return 100.0
    
    # Handle numeric scores with + or -
    if '+' in score_str:
        base_score = float(re.findall(r'\d+\.?\d*', score_str)[0])
        return base_score + 0.3  # Add jitter for +
    elif '-' in score_str and not score_str.startswith('-'):
        base_score = float(re.findall(r'\d+\.?\d*', score_str)[0])
        return base_score - 0.3  # Subtract jitter for -
    else:
        try:
            return float(score_str)
        except ValueError:
            # Try to extract first number if complex format
            numbers = re.findall(r'\d+\.?\d*', score_str)
            if numbers:
                return float(numbers[0])
            return None

def render_lead_event(event_df, event_name):
    """Render lead event analysis with scatter plots."""
    st.subheader(f"🧗 Lead: {event_df[event_df['location'] == event_name]['event_name'].iloc[0]}")
    
    rounds = ['Qualification', 'Semi-Final', 'Final']
    available_rounds = [r for r in rounds if r in event_df['round'].unique()]
    if not available_rounds:
        st.warning("No round data available")
        return
    
    # Progression info
    progression_info = {}
    for i, round_name in enumerate(available_rounds[:-1]):
        next_round = available_rounds[i + 1]
        next_athletes = set(event_df[event_df['round'] == next_round]['name'].unique())
        progression_info[round_name] = next_athletes
    
    n_rounds = len(available_rounds)
    fig = make_subplots(
        rows=1, cols=n_rounds,
        subplot_titles=available_rounds,
        shared_yaxes=True
    )
    
    for idx, round_name in enumerate(available_rounds, 1):
        round_df = event_df[event_df['round'] == round_name].copy()
        if round_df.empty:
            continue
        
        scores, athletes, progresses = [], [], []
        for _, row in round_df.iterrows():
            athlete_name = row['name']
            score = None
            for score_col in ['route_1', 'route_2', 'round_score']:
                if score_col in row and pd.notna(row[score_col]):
                    score = parse_lead_score(row[score_col])
                    if score is not None:
                        break
            
            if score is not None:
                scores.append(score)
                athletes.append(athlete_name)
                if round_name in progression_info:
                    progresses.append(athlete_name in progression_info[round_name])
                else:
                    progresses.append(False)
        
        if scores:
            from collections import defaultdict
            import numpy as np
            
            # Group athletes by 5-point score ranges
            score_bins = defaultdict(list)
            for i, score in enumerate(scores):
                bin_key = int(score // 5) * 5  # Round down to nearest 5
                score_bins[bin_key].append(i)
            
            # Generate x-positions: vertical alignment with jitter for multiple athletes
            x_positions = [0] * len(scores)              
            if round_name != "Final":
                for bin_key, athlete_indices in score_bins.items():
                    if len(athlete_indices) > 1:
                        sorted_indices = sorted(athlete_indices, key=lambda i: scores[i])
                        
                        for j, athlete_idx in enumerate(sorted_indices):
                            if j == 0:
                                x_positions[athlete_idx] = 0  # Lowest stays at center
                            else:
                                offset = (j + 1) // 2 * 0.3
                                if j % 2 == 1: 
                                    x_positions[athlete_idx] = offset
                                else: 
                                    x_positions[athlete_idx] = -offset
            
            # Assign colors based on round and performance
            if round_name == "Final":
                score_ranking = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
                medal_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]  # Gold, Silver, Bronze
                colors = []

                for i in range(len(scores)):
                    rank = score_ranking.index(i)
                    if rank < 3:
                        colors.append(medal_colors[rank])
                    else:
                        colors.append("#708090")  # Gray for others

                # Add legend entries for top 3 athletes
                for rank, medal in enumerate(["Gold", "Silver", "Bronze"]):
                    top_idx = score_ranking[rank]
                    fig.add_trace(
                        go.Scatter(
                            x=[None],
                            y=[None],
                            mode='markers+text',
                            marker=dict(color=medal_colors[rank], size=12, line=dict(width=1, color="white")),
                            name=f"{athletes[top_idx]}",
                            showlegend=True
                        )
                    )
            else:
                # Progression colors
                colors = ['#2E8B57' if prog else '#DC143C' for prog in progresses]

            hover_text = [f"{athlete}<br>Score: {score:.1f}" for athlete, score in zip(athletes, scores)]
            
            fig.add_trace(
                go.Scatter(
                    x=x_positions,
                    y=scores,
                    mode='markers',
                    marker=dict(
                        color=colors,
                        size=12,
                        opacity=0.8,
                        line=dict(width=1, color="white")
                    ),
                    text=hover_text,
                    hoverinfo='text',
                    showlegend=False
                ),
                row=1, col=idx
            )
    
    fig.update_layout(
        title=f"Lead Scores by Round - {event_name}",
        height=650,
        showlegend=True,
        yaxis=dict(title="Score", titlefont=dict(size=16), tickfont=dict(size=12))
    )
    
    for idx in range(1, n_rounds + 1):
        fig.update_xaxes(showticklabels=False, row=1, col=idx)
    
    st.plotly_chart(fig)
