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
    # render_performance_timeline(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode)
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
    
    st.plotly_chart(fig)


# def render_discipline_round_analysis(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
#     """Render combined discipline and round performance analysis with funnel charts."""
#     st.subheader("Performance by Discipline & Round")
    
#     # Only show Boulder and Lead disciplines
#     disciplines_to_show = ['Boulder', 'Lead']
    
#     # Get available disciplines for each athlete
#     primary_disciplines = set(primary_df['discipline'].unique()) if not primary_df.empty else set()
#     comparison_disciplines = set(comparison_df['discipline'].unique()) if comparison_mode and not comparison_df.empty else set()
    
#     if comparison_mode:
#         available_disciplines = primary_disciplines.union(comparison_disciplines)
#     else:
#         available_disciplines = primary_disciplines
    
#     # Filter to only Boulder and Lead
#     disciplines_to_display = [d for d in disciplines_to_show if d in available_disciplines]
    
#     if not disciplines_to_display:
#         st.warning("No Boulder or Lead discipline data available")
#         return
    
#     print(primary_df.columns) => ['name', 'country', 'round_rank', 'round_score', 'event_name',
#        'event_id', 'year', 'location', 'discipline', 'gender', 'round',
#        'start_date', 'category_round_results', 'event_results', 'p1_top',
#        'p1_zone', 'p2_top', 'p2_zone', 'p3_top', 'p3_zone', 'p4_top',
#        'p4_zone', 'p5_top', 'p5_zone', 'source_file', '_file', 'file_path',
#        'route_1', '1/8_winner', '1/8_time', '1/4_winner', '1/4_time',
#        '1/2_winner', '1/2_time', 'final_winner', 'final_time',
#        'small_final_winner', 'small_final_time', 'route_2', 'quali_time_a',
#        'quali_time_b', 'boulder_score', 'boulder_rank', 'lead_score',
#        'lead_rank', 'processed_at', 'scoring_era']
#     # create metrics before the funnel chart
#     # for boulder,
#     # add total events participated, # add % progression to the semis and finals
#     # Add number of p{num}_tops in round(qualis, semis, finals), as well as % e.g 200 tops (60%)
#     # Add number of avg attempts in round(qualis, semis, finals)
#     # for lead,
#     # add total events participated, # add % progression to the semis and finals
#     # Add number of avg_score in qualis, semis, finals.
    
#     # LET'S CHANGE FUNNEL CHART TO SEPARATE FUNNEL CHARTS FOR EACH ATHELETE AND EACH DISCIPLINE,
#     # EACH CHART STILL SHOW COMPETITIONS IN QUALI, SEMI, FINAL AS PROGRESSION TOWARDS NEXT ROUNDS
    
#     # Create funnel chart for each discipline
#     for discipline in disciplines_to_display:
#         # Prepare funnel data
#         funnel_data = []
#         round_order = ['Qualification', 'Semi-Final', 'Final']
        
#         # Primary athlete data
#         primary_disc_data = primary_df[primary_df['discipline'] == discipline]
#         for round_name in round_order:
#             round_data = primary_disc_data[primary_disc_data['round'] == round_name]
#             if not round_data.empty and 'round_rank' in round_data.columns:
#                 rank_data = round_data.dropna(subset=['round_rank'])
#                 if not rank_data.empty:
#                     funnel_data.append({
#                         'competitions': len(rank_data),
#                         'round': round_name,
#                         'athlete': primary_athlete,
#                         'avg_rank': rank_data['round_rank'].mean()
#                     })
        
#         # Comparison athlete data
#         if comparison_mode:
#             comparison_disc_data = comparison_df[comparison_df['discipline'] == discipline]
#             for round_name in round_order:
#                 round_data = comparison_disc_data[comparison_disc_data['round'] == round_name]
#                 if not round_data.empty and 'round_rank' in round_data.columns:
#                     rank_data = round_data.dropna(subset=['round_rank'])
#                     if not rank_data.empty:
#                         funnel_data.append({
#                             'competitions': len(rank_data),
#                             'round': round_name,
#                             'athlete': comparison_athlete,
#                             'avg_rank': rank_data['round_rank'].mean()
#                         })
        
#         if funnel_data:
#             funnel_df = pd.DataFrame(funnel_data)
            
#             # Create funnel chart
#             fig = px.funnel(
#                 funnel_df, 
#                 x='competitions', 
#                 y='round', 
#                 color='athlete',
#                 title=f"{discipline} - Competition Progression",
#                 color_discrete_map={primary_athlete: '#1f77b4', comparison_athlete: '#ff7f0e'} if comparison_mode else {primary_athlete: '#1f77b4'},
#                 text='competitions'
#             )

#             # Remove 3D effects by updating layout
#             fig.update_layout(height=400)

#             # Make funnel bars flat (remove any 3D styling)
#             fig.update_traces(textinfo='text', textposition='inside', textfont_size=16)
#             st.plotly_chart(fig)
#         else:
#             st.info(f"No round data available for {discipline}")

def render_discipline_round_analysis(primary_df, comparison_df, primary_athlete, comparison_athlete, comparison_mode):
    """Render combined discipline and round performance analysis with metrics and separate funnel charts."""
    st.subheader("Performance by Discipline & Round")
    def display_discipline_metrics(disc_data, discipline):
        """Display discipline-specific metrics."""
        if disc_data.empty:
            st.metric("Status", "No data available")
            return
        
        # Total events participated and progression percentages in one column
        total_events = len(disc_data)
        quali_count = len(disc_data[disc_data['round'] == 'Qualification'])
        semi_count = len(disc_data[disc_data['round'] == 'Semi-Final'])
        final_count = len(disc_data[disc_data['round'] == 'Final'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Events", total_events)
        with col2:
            if quali_count > 0:
                semi_progression = (semi_count / quali_count * 100) if quali_count > 0 else 0
                st.metric("Progression to Semis", f"{semi_progression:.1f}%")
        with col3:
            if quali_count > 0:
                final_progression = (final_count / quali_count * 100) if quali_count > 0 else 0
                st.metric("Progression to Finals", f"{final_progression:.1f}%")
        
        if discipline == 'Boulder':
            display_boulder_metrics(disc_data)
        elif discipline == 'Lead':
            display_lead_metrics(disc_data)

    def display_boulder_metrics(disc_data):
        """Display Boulder-specific metrics."""
        rounds = ['Qualification', 'Semi-Final', 'Final']
        
        for round_name in rounds:
            round_data = disc_data[disc_data['round'] == round_name]
            if round_data.empty:
                continue

            # Calculate overall averages for all problems
            all_tops_percentages = []
            all_attempts = []
            total_top_counts = 0
            total_problems = 0

            for i in range(1, 6):  # P1 to P5
                top_col = f'p{i}_top'

                if top_col in round_data.columns:
                    # Count tops (not 'X')
                    top_counts = round_data[top_col].apply(lambda x: x != 'X' if pd.notna(x) else False).sum()
                    problem_count = round_data[top_col].notna().sum()

                    total_top_counts += top_counts
                    total_problems += problem_count

                    if problem_count > 0:
                        top_percentage = (top_counts / problem_count) * 100
                        all_tops_percentages.append(top_percentage)

                        # Calculate average attempts for successful tops
                        successful_attempts = round_data[round_data[top_col] != 'X'][top_col]
                        if not successful_attempts.empty:
                            avg_attempts = pd.to_numeric(successful_attempts, errors='coerce').mean()
                            if pd.notna(avg_attempts):
                                all_attempts.append(avg_attempts)

            # Display averages as metrics in columns
            if all_tops_percentages:
                avg_top_percentage = sum(all_tops_percentages) / len(all_tops_percentages)
                avg_attempts_overall = sum(all_attempts) / len(all_attempts) if all_attempts else 0

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader(round_name)
                with col2:
                    st.metric("Top", f"{total_top_counts} ({avg_top_percentage:.0f}%)")
                with col3:
                    st.metric("Avg Attempts", f"{avg_attempts_overall:.1f}")



    def display_lead_metrics(disc_data):
        """Display Lead-specific metrics."""
        rounds = ['Qualification', 'Semi-Final', 'Final']
        round_metrics = []

        for round_name in rounds:
            round_data = disc_data[disc_data['round'] == round_name]
            if round_data.empty:
                continue

            # Check for route scores
            route_cols = ['route_1', 'route_2']
            all_scores = []

            for route_col in route_cols:
                if route_col in round_data.columns:
                    scores = round_data[route_col].dropna()
                    if not scores.empty:
                        # Try to extract numeric values from scores like "45.5" or "Top"
                        for score in scores:
                            if str(score).lower() == 'top':
                                all_scores.append(100)
                            else:
                                try:
                                    all_scores.append(float(str(score).split()[0]))
                                except:
                                    continue

            if all_scores:
                avg_score = sum(all_scores) / len(all_scores)
                round_metrics.append((round_name, avg_score))

        # --- Display all collected metrics in one row ---
        if round_metrics:
            st.markdown("Average Scores by Round")
            cols = st.columns(len(round_metrics))
            for col, (round_name, avg_score) in zip(cols, round_metrics):
                col.metric(f"{round_name}", f"{avg_score:.1f}")

                    
    def create_separate_funnels(primary_data, comparison_data, primary_athlete, comparison_athlete, discipline, comparison_mode):
        """Create separate funnel charts for each athlete."""
        
        def create_funnel_data(athlete_data, athlete_name):
            funnel_data = []
            round_order = ['Qualification', 'Semi-Final', 'Final']
            
            for round_name in round_order:
                round_data = athlete_data[athlete_data['round'] == round_name]
                if not round_data.empty and 'round_rank' in round_data.columns:
                    rank_data = round_data.dropna(subset=['round_rank'])
                    if not rank_data.empty:
                        funnel_data.append({
                            'competitions': len(rank_data),
                            'round': round_name,
                            'athlete': athlete_name,
                            'avg_rank': rank_data['round_rank'].mean()
                        })
            
            return pd.DataFrame(funnel_data) if funnel_data else pd.DataFrame()
        
        # Create funnel data
        primary_funnel = create_funnel_data(primary_data, primary_athlete)
        comparison_funnel = create_funnel_data(comparison_data, comparison_athlete) if comparison_mode else pd.DataFrame()
        
        if comparison_mode and not comparison_funnel.empty and not primary_funnel.empty:
            # Side by side funnels
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = px.funnel(
                    primary_funnel, 
                    x='competitions', 
                    y='round',
                    title=f"{primary_athlete} - {discipline}",
                    color_discrete_sequence=['#1f77b4'],
                    text='competitions'
                )
                fig1.update_traces(textinfo='text', textposition='inside', textfont_size=16)
                fig1.update_layout(height=400)
                st.plotly_chart(fig1)
            
            with col2:
                fig2 = px.funnel(
                    comparison_funnel, 
                    x='competitions', 
                    y='round',
                    title=f"{comparison_athlete} - {discipline}",
                    color_discrete_sequence=['#ff7f0e'],
                    text='competitions'
                )
                fig2.update_traces(textinfo='text', textposition='inside', textfont_size=16)
                fig2.update_layout(height=400)
                st.plotly_chart(fig2)
                
        elif not primary_funnel.empty:
            # Single funnel
            fig = px.funnel(
                primary_funnel, 
                x='competitions', 
                y='round',
                title=f"{primary_athlete} - {discipline}",
                color_discrete_sequence=['#1f77b4'],
                text='competitions'
            )
            fig.update_traces(textinfo='text', textposition='inside', textfont_size=16)
            fig.update_layout(height=400)
            st.plotly_chart(fig)
        else:
            st.info(f"No round data available for {discipline}")
    
    # Main function logic
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
    
    # Create metrics and funnel charts for each discipline
    for discipline in disciplines_to_display:
        st.write(f"### {discipline}")
        
        # Get discipline data
        primary_disc_data = primary_df[primary_df['discipline'] == discipline] if not primary_df.empty else pd.DataFrame()
        comparison_disc_data = comparison_df[comparison_df['discipline'] == discipline] if comparison_mode and not comparison_df.empty else pd.DataFrame()
        
        # Display metrics
        if comparison_mode:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<span style='color: #1f77b4;'>{primary_athlete} Metrics</span>", unsafe_allow_html=True)
                display_discipline_metrics(primary_disc_data, discipline)
            with col2:
                st.markdown(f"<span style='color: #ff7f0e;'>{comparison_athlete} Metrics</span>", unsafe_allow_html=True)
                display_discipline_metrics(comparison_disc_data, discipline)
        else:
            display_discipline_metrics(primary_disc_data, discipline)
        
        # Create separate funnel charts
        create_separate_funnels(primary_disc_data, comparison_disc_data, primary_athlete, comparison_athlete, discipline, comparison_mode)


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


        # # Plot choropleth
        # fig = px.choropleth(
        #     merged_stats,
        #     locations='country',
        #     locationmode='country names',
        #     color='best_avg_rank',
        #     hover_name='hover_label',
        #     hover_data=[f'avg_rank_{primary_athlete}', f'avg_rank_{comparison_athlete}', 'country'],
        #     color_continuous_scale='Sunset',
        #     range_color=[np.nanmax(merged_stats['best_avg_rank']), np.nanmin(merged_stats['best_avg_rank'])],
        #     title=f"{primary_athlete} vs {comparison_athlete} - Best Athlete by Country",
        # )

        # fig.update_layout(
        #     height=600,
        #     margin=dict(l=20, r=20, t=50, b=20),
        #     paper_bgcolor="#1e1e1e",
        #     plot_bgcolor="#1e1e1e",
        # )

        # fig.update_traces(
        #     marker_line_color='black',  # optional: add borders to countries
        #     selector=dict(type='choropleth')
        # )
        # fig.update_geos(
        #     projection_type="natural earth",
        #     # lataxis_range=[-10, 80],
        #     bgcolor="rgba(30,30,30,1)",  # dark background
        #     showcoastlines=True,
        #     coastlinecolor="gray",
        #     showland=True,
        #     landcolor="rgba(50,50,50,1)",  # countries with no data
        #     showocean=True,
        #     oceancolor="#111111"
        # )
        # Map discrete colors
        color_map = {
            primary_athlete: "#1f77b4",      # Primary
            comparison_athlete: "#ff7f0e"    # Comparison
        }

        # Plot choropleth with discrete colors
        fig = px.choropleth(
            merged_stats,
            locations="country",
            locationmode="country names",
            color="best_athlete",   # categorical color
            hover_name="hover_label",
            hover_data=[f"avg_rank_{primary_athlete}", f"avg_rank_{comparison_athlete}", "country"],
            title=f"{primary_athlete} vs {comparison_athlete} - Best Athlete by Country",
            color_discrete_map=color_map
        )

        fig.update_layout(
            height=600,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="#1e1e1e",
            plot_bgcolor="#1e1e1e",
        )

        fig.update_traces(
            marker_line_color="black",  # add borders to countries
            selector=dict(type="choropleth")
        )

        fig.update_geos(
            projection_type="natural earth",
            bgcolor="rgba(30,30,30,1)",  # dark background
            showcoastlines=True,
            coastlinecolor="gray",
            showland=True,
            landcolor="rgba(50,50,50,1)",  # countries with no data
            showocean=True,
            oceancolor="#111111"
        )
        st.plotly_chart(fig)

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

            st.plotly_chart(fig)