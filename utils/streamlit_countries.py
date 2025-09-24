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
    # st.subheader("Participation Overview")
    
    # col1, col2, col3 = st.columns(3)
    
    # Country participation metrics
    country_stats = filtered_df.groupby('country').agg({
        'name': 'nunique',
        'year': ['nunique', 'min', 'max'],
        'event_name': 'nunique'
    }).round(2)
    
    country_stats.columns = ['athletes', 'years_active', 'first_year', 'last_year', 'events']
    country_stats = country_stats.reset_index()
    country_stats['flag'] = country_stats['country'].apply(get_flag_emoji)
    
    # with col1:
    #     st.metric("Total Countries", len(country_stats))
    
    # with col2:
    #     avg_athletes = country_stats['athletes'].mean()
    #     st.metric("Avg Athletes per Country", f"{avg_athletes:.1f}")
    
    # with col3:
    #     total_athletes = country_stats['athletes'].sum()
    #     st.metric("Total Athlete Participations", f"{total_athletes:,}")
    
    # all_flags = " ".join(country_stats['flag'].tolist())

    # # Display below the metrics
    # st.markdown(f"<p style='font-size:30px'>{all_flags}</p>", unsafe_allow_html=True)
    st.subheader("Global Statistics")
    map_metric = st.pills(
        "Choose metric to display on map:",
        ["Number of Athletes", "Number of Events Participated", "Average Rank", "Podiums Finished"],
        default="Number of Athletes",
        label_visibility='hidden',
    )

    # Prepare data based on selected metric
    if map_metric == "Number of Athletes":
        map_data = country_stats.copy()
        color_column = "athletes"
        color_label = "Athlete Count"
        title_suffix = "Athlete Participation"
        color_scale = "Sunset"
        
    elif map_metric == "Number of Events Participated":
        map_data = country_stats.copy()
        color_column = "events"
        color_label = "Event Count"
        title_suffix = "Event Participation"
        color_scale = "Sunset"
        
    elif map_metric == "Average Rank":
        if 'round_rank' in filtered_df.columns:
            performance_df = filtered_df.dropna(subset=['round_rank'])
            country_performance = performance_df.groupby('country').agg({
                'round_rank': 'mean'
            }).round(2)
            country_performance.columns = ['avg_rank']
            country_performance = country_performance.reset_index()
            
            # Filter for countries with at least 10 competitions
            min_competitions = performance_df.groupby('country').size()
            countries_with_enough_data = min_competitions[min_competitions >= 10].index
            country_performance = country_performance[country_performance['country'].isin(countries_with_enough_data)]
            
            map_data = country_performance.copy()
            color_column = "avg_rank"
            color_label = "Average Rank"
            title_suffix = "Average Performance"
            color_scale = "RdYlGn_r"  # Reversed so lower ranks (better) are green
        else:
            st.warning("Performance data not available")
            map_data = country_stats.copy()
            color_column = "athletes"
            color_label = "Athlete Count"
            title_suffix = "Athlete Participation"
            color_scale = "Sunset"

    elif map_metric == "Podiums Finished":
        if 'round_rank' in filtered_df.columns:
            performance_df = filtered_df.dropna(subset=['round_rank'])
            podium_df = performance_df[performance_df['round_rank'] <= 3]
            podium_counts = podium_df.groupby('country').size().reset_index(name='total_podiums')
            
            map_data = podium_counts.copy()
            color_column = "total_podiums"
            color_label = "Total Podiums"
            title_suffix = "Podium Finishes"
            color_scale = "RdYlGn_r"
        else:
            st.warning("Performance data not available")
            map_data = country_stats.copy()
            color_column = "athletes"
            color_label = "Athlete Count"
            title_suffix = "Athlete Participation"
            color_scale = "Sunset"

    # Add flag for hover
    map_data['flag'] = map_data['country'].apply(get_flag_emoji)
    map_data['country_flag'] = map_data['flag'] + ' ' + map_data['country']

    # Create the map
    fig_map = px.choropleth(
        map_data,
        locations="country",
        color=color_column,
        hover_name="country_flag",
        hover_data={color_column: True},
        color_continuous_scale=color_scale,
        labels={color_column: color_label},
        title=f"{title_suffix} by Country",
    )

    # Dark theme + styling
    fig_map.update_layout(
        height=600,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        coloraxis_colorbar=dict(
            title=color_label,
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

    st.plotly_chart(fig_map)
    
   








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
    st.plotly_chart(fig_growth)
    
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
    
    st.dataframe(display_stats)
    