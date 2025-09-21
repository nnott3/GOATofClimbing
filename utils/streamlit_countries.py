import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import numpy as np

# Country code to flag emoji mapping
COUNTRY_FLAGS = {
    'USA': '🇺🇸', 'FRA': '🇫🇷', 'GER': '🇩🇪', 'JPN': '🇯🇵', 'GBR': '🇬🇧',
    'ITA': '🇮🇹', 'AUT': '🇦🇹', 'CAN': '🇨🇦', 'SUI': '🇨🇭', 'ESP': '🇪🇸',
    'RUS': '🇷🇺', 'SLO': '🇸🇮', 'BEL': '🇧🇪', 'CZE': '🇨🇿', 'NOR': '🇳🇴',
    'POL': '🇵🇱', 'SWE': '🇸🇪', 'NED': '🇳🇱', 'KOR': '🇰🇷', 'AUS': '🇦🇺',
    'CHN': '🇨🇳', 'UKR': '🇺🇦', 'SVK': '🇸🇰', 'FIN': '🇫🇮', 'DEN': '🇩🇰',
    'CRO': '🇭🇷', 'ISR': '🇮🇱', 'IND': '🇮🇳', 'RSA': '🇿🇦', 'BRA': '🇧🇷',
    'ARG': '🇦🇷', 'CHI': '🇨🇱', 'MEX': '🇲🇽', 'COL': '🇨🇴', 'PER': '🇵🇪',
    'THA': '🇹🇭', 'MAS': '🇲🇾', 'SGP': '🇸🇬', 'PHI': '🇵🇭', 'IND': '🇮🇩',
    'NZL': '🇳🇿', 'ISL': '🇮🇸', 'IRL': '🇮🇪', 'POR': '🇵🇹', 'HUN': '🇭🇺',
    'ROU': '🇷🇴', 'BUL': '🇧🇬', 'LTU': '🇱🇹', 'LAT': '🇱🇻', 'EST': '🇪🇪',
    'AZE': '🇦🇿', 'BIH': '🇧🇦', 'BLR': '🇧🇾', 'BOL': '🇧🇴', 'BRN': '🇧🇳',
    'BWA': '🇧🇼', 'CAM': '🇰🇲', 'CFR': '🇨🇫', 'CRC': '🇨🇷', 'CYP': '🇨🇾',
    'ECU': '🇪🇨', 'ESA': '🇸🇻', 'GEO': '🇬🇪', 'GRE': '🇬🇷', 'GTM': '🇬🇹',
    'GUA': '🇬🇺', 'GUM': '🇬🇺', 'HKG': '🇭🇰', 'HND': '🇭🇳', 'HON': '🇭🇳',
    'IRI': '🇮🇷', 'IRQ': '🇮🇶', 'JOR': '🇯🇴', 'KAZ': '🇰🇿', 'KGZ': '🇰🇬',
    'KSA': '🇸🇦', 'KUW': '🇰🇼', 'LBN': '🇱🇧', 'LKA': '🇱🇰', 'LUX': '🇱🇺',
    'MAC': '🇲🇴', 'MGL': '🇲🇳', 'MKD': '🇲🇰', 'MRI': '🇲🇷', 'MYS': '🇲🇾',
    'NEP': '🇳🇵', 'PAK': '🇵🇰', 'PHL': '🇵🇭', 'PRT': '🇵🇹', 'PUR': '🇵🇷',
    'SRB': '🇷🇸', 'SRI': '🇱🇰', 'TPE': '🇹🇼', 'TUR': '🇹🇷', 'UGA': '🇺🇬',
    'UZB': '🇺🇿', 'VEN': '🇻🇪', 'ZAF': '🇿🇦', 'BRU': '🇧🇳', 'LVA': '🇱🇻',
    'AND': '🇦🇩', 'MNE': '🇲🇪', 'SMR': '🇸🇲', 'VIE': '🇻🇳', 'YEM': '🇾🇪',
    'INA': '🇮🇩', 'TUN': '🇹🇳', 'ALG': '🇩🇿', 'MAR': '🇲🇦', 'NGA': '🇳🇬',
    'IDN': '🇮🇩',

}

def get_flag_emoji(country_code):
    """Get flag emoji for country code, return country code if not found."""
    return COUNTRY_FLAGS.get(country_code, "")

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
    """Render the country analytics dashboard."""
    
    st.header("Country Performance Analytics")
    
    # Load data
    df = load_data()
    if df is None or df.empty:
        st.error("No competition data available")
        return
    
    # Clean and prepare data
    df = df.dropna(subset=['name', 'year', 'discipline', 'gender', 'country'])
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df = df.dropna(subset=['year'])
    
    if 'round_rank' in df.columns:
        df['round_rank'] = pd.to_numeric(df['round_rank'], errors='coerce')
    
    col1, col2, col3 = st.columns([1.2, 1, 2])

    with col1:
        disciplines = ['All'] + sorted([d for d in df['discipline'].unique() if d not in ['Combined','Boulder&lead']])
        selected_discipline = st.segmented_control(
            "Discipline", disciplines, default="All"
        )

    with col2:
        genders = ['All'] + sorted(df['gender'].unique().tolist())
        selected_gender = st.segmented_control(
            "Gender", genders, default="All"
        )

    with col3:
        year_range = st.slider(
            "Year Range",
            min_value=int(df['year'].min()),
            max_value=int(df['year'].max()),
            value=(int(df['year'].min()), int(df['year'].max()))
        )
   
   # Apply filters
    filtered_df = df[
        (df['year'] >= year_range[0]) & 
        (df['year'] <= year_range[1])
    ]
    
    if selected_discipline != 'All':
        filtered_df = filtered_df[filtered_df['discipline'] == selected_discipline]
    
    if selected_gender != 'All':
        filtered_df = filtered_df[filtered_df['gender'] == selected_gender]
    
    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
        return

    # Country participation overview
    st.subheader("Participation Overview")
    
    col1, col2, col3 = st.columns(3)
    
    # Country participation metrics
    country_stats = filtered_df.groupby('country').agg({
        'name': 'nunique',
        'year': ['nunique', 'min', 'max'],
        'event_name': 'nunique'
    }).round(2)
    
    country_stats.columns = ['athletes', 'years_active', 'first_year', 'last_year', 'events']
    country_stats = country_stats.reset_index()
    country_stats['flag'] = country_stats['country'].apply(get_flag_emoji)
    
    with col1:
        st.metric("Total Countries", len(country_stats))
    
    with col2:
        avg_athletes = country_stats['athletes'].mean()
        st.metric("Avg Athletes per Country", f"{avg_athletes:.1f}")
    
    with col3:
        total_athletes = country_stats['athletes'].sum()
        st.metric("Total Athlete Participations", f"{total_athletes:,}")
    
    # all_flags = " ".join(country_stats['flag'].tolist())

    # # Display below the metrics
    # st.markdown(f"<p style='font-size:30px'>{all_flags}</p>", unsafe_allow_html=True)
    # --- Create choropleth map of athlete counts ---
    country_stats['country flag'] = country_stats['flag'] + ' ' + country_stats['country']
    fig_map = px.choropleth(
        country_stats,
        locations="country",             # ISO-3 country codes
        color="athletes",                # number of athletes
        hover_name="country flag",       # show flag + name on hover
        hover_data={"athletes": True},   # show athlete count
        color_continuous_scale="Sunset", # warm colors for counts
        labels={"athletes": "Athlete Count"},
        title=f"Athlete Participation by Country",
    )

    # Dark theme + styling
    fig_map.update_layout(
        height=600,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        coloraxis_colorbar=dict(
            title="Athletes",
            ticks="outside",
        )
    )

    fig_map.update_traces(
        marker_line_color="black",
        selector=dict(type="choropleth")
    )

    fig_map.update_geos(
        projection_type="natural earth",
        bgcolor="rgba(30,30,30,1)",
        showcoastlines=True,
        coastlinecolor="gray",
        showland=True,
        landcolor="rgba(50,50,50,1)",
        showocean=True,
        oceancolor="#111111"
    )

    st.plotly_chart(fig_map, use_container_width=True)



















    # Top participating countries
    st.subheader("Top Participating Countries")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Bar chart of top countries
        top_n = 8
        top_countries = country_stats.nlargest(top_n, 'athletes')
        top_countries['country_flag'] = top_countries['flag'] + ' ' + top_countries['country']
        
        fig_participation = px.bar(
            top_countries,
            x='athletes',
            y='country_flag',
            orientation='h',
            title=f'Top {top_n} Countries by Athlete Count',
            labels={'athletes': 'Number of Athletes', 'country_flag': 'Country'}
        )
        fig_participation.update_layout(height=500, yaxis={'categoryorder':'total ascending', 'tickfont':dict(size=22)})
        st.plotly_chart(fig_participation, width='stretch')
    
    with col_right:
        # Events participation
        fig_events = px.bar(
            top_countries,
            x='events',
            y='country_flag',
            orientation='h',
            title=f'Top {top_n} Countries by Event Participation',
            labels={'events': 'Number of Events', 'country_flag': 'Country'}
        )
        fig_events.update_layout(height=500, yaxis={'categoryorder':'total ascending', 'tickfont':dict(size=22)})
        
        st.plotly_chart(fig_events, width='stretch')
    
    # Performance analysis (if rank data available)
    if 'round_rank' in filtered_df.columns:
        st.subheader("Performance Analysis")
        
        # Calculate performance metrics
        performance_df = filtered_df.dropna(subset=['round_rank'])
        country_performance = performance_df.groupby('country').agg({
            'round_rank': ['mean', 'median', 'count'],
            'name': 'nunique'
        }).round(2)
        
        country_performance.columns = ['avg_rank', 'median_rank', 'competitions', 'athletes']
        country_performance = country_performance.reset_index()
        country_performance = country_performance[country_performance['competitions'] >= 10]  # Filter for meaningful sample size
        country_performance['flag'] = country_performance['country'].apply(get_flag_emoji)
        country_performance['country_flag'] = country_performance['flag'] + ' ' + country_performance['country']
        
        # Podium analysis
        podium_df = performance_df[performance_df['round_rank'] <= 3]
        podium_counts = podium_df.groupby(['country', 'round_rank']).size().unstack(fill_value=0)
        podium_counts.columns = [f'Rank_{int(col)}' for col in podium_counts.columns]
        podium_counts['total_podiums'] = podium_counts.sum(axis=1)
        podium_counts = podium_counts.reset_index()
        podium_counts['flag'] = podium_counts['country'].apply(get_flag_emoji)
        
        col_perf1, col_perf2 = st.columns(2)
        
        with col_perf1:
            # Average ranking performance
            best_avg_rank = country_performance.nsmallest(8, 'avg_rank')
            
            fig_avg_rank = px.bar(
                best_avg_rank,
                x='avg_rank',
                y='country_flag',
                orientation='h',
                title='Best Average Rankings',
                labels={'avg_rank': 'Average Rank', 'country_flag': 'Country'}
            )
            fig_avg_rank.update_layout(height=500, yaxis={'categoryorder':'total descending', 'tickfont':dict(size=22)})
            st.plotly_chart(fig_avg_rank, width='stretch')
        
        with col_perf2:
            # Podium counts
            if not podium_counts.empty:
                top_podium = podium_counts.nlargest(8, 'total_podiums')
                top_podium['country_flag'] = top_podium['flag'] + ' ' + top_podium['country']
                
                fig_podiums = px.bar(
                    top_podium,
                    x='total_podiums',
                    y='country_flag',
                    orientation='h',
                    title='Most Podium Finishes',
                    labels={'total_podiums': 'Total Podiums', 'country_flag': 'Country'}
                )
                fig_podiums.update_layout(height=500, yaxis={'categoryorder':'total ascending', 'tickfont':dict(size=22)})
                st.plotly_chart(fig_podiums, width='stretch')
    
    # Growth trends over time
    st.subheader("Growth Trends")
    
    # Athletes per year by top countries
    yearly_participation = filtered_df.groupby(['year', 'country'])['name'].nunique().reset_index()
    yearly_participation.rename(columns={'name': 'athletes'}, inplace=True)
    
    # Get top 8 countries for cleaner visualization
    top_8_countries = country_stats.nlargest(8, 'athletes')['country'].tolist()
    yearly_top = yearly_participation[yearly_participation['country'].isin(top_8_countries)]
    
    fig_growth = px.line(
        yearly_top,
        x='year',
        y='athletes',
        color='country',
        title='Athlete Participation Growth - Top 8 Countries',
        markers=True
    )
    fig_growth.update_layout(height=500)
    st.plotly_chart(fig_growth, width='stretch')
    
    # Country comparison table
    st.subheader("Detailed Country Statistics")
    
    # Enhanced country statistics
    detailed_stats = country_stats.copy()
    detailed_stats['years_span'] = detailed_stats['last_year'] - detailed_stats['first_year'] + 1
    detailed_stats['athletes_per_year'] = (detailed_stats['athletes'] / detailed_stats['years_active']).round(1)
    
    # Format for display
    display_stats = detailed_stats[
        ['flag', 'country', 'athletes', 'events', 'years_active', 'first_year', 'last_year', 'athletes_per_year']
    ].sort_values('athletes', ascending=False)
    
    display_stats.columns = [
        'Flag', 'Country', 'Athletes', 'Events', 'Years Active', 
        'First Year', 'Last Year', 'Athletes/Year'
    ]

    display_stats.reset_index(drop=True, inplace=True)
    
    st.dataframe(display_stats, width='stretch')
    