# import streamlit as st
# import pandas as pd
# import sys
# import os
# from pathlib import Path
# import warnings


# # Import modules from utils folder
# try:
#     from utils.scraper_init import IFSCScraper
#     from utils.main import IFSCDataManager  
#     from utils.data_aggregator import IFSCDataAggregator
#     from utils.elo_scoring import ELOCalculator
#     from utils import streamlit_elo   
# except ImportError as e:
#     st.error(f"Import error: {e}")
#     st.error("Please ensure all modules are in the 'utils/' directory")
#     st.stop()

# warnings.filterwarnings('ignore')

# # Page configuration
# st.set_page_config(
#     page_title="Climbing Competition Analysis",
#     page_icon="🧗‍♂️",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# @st.cache_resource
# def load_components():
#     """Initialize analysis components."""
#     try:
#         aggregator = IFSCDataAggregator()
#         calculator = ELOCalculator()
#         return aggregator, calculator
#     except Exception as e:
#         st.error(f"Error initializing components: {e}")
#         return None, None

# def check_data_availability():
#     """Check if required data files exist."""
#     required_paths = [
#         Path("Data/aggregate_data"),
#     ]
    
#     missing_paths = [p for p in required_paths if not p.exists()]
    
#     if missing_paths:
#         st.error("Missing required data directories:")
#         for path in missing_paths:
#             st.write(f"- {path}")
        
#         st.markdown("""
#         Data/
#         └── aggregate_data/
#             ├── aggregated_results.csv
#             └── [era-specific files].csv

#         Elo_Data/
#         ├── elo_history.csv

#         utils/
#         ├── scraper_init.py => IFSCScraper
#         ├── main.py => IFSCDataManager, 
#         ├── data_aggregator.py => IFSCDataAggregator
#         ├── analysis.py => ClimbingAnalyzer
#         ├── elo_scoring.py => ELOCalculator
#         ├── streamlit_elo.py

#         app.py
#         """)
#         return False
    
#     return True

# def get_data_overview():
#     """Get basic data overview."""
#     try:
#         agg_file = Path("Data/aggregate_data/aggregated_results.csv")
#         if not agg_file.exists():
#             return {}
        
#         df = pd.read_csv(agg_file)
#         if df.empty:
#             return {}
        
#         overview = {
#             'total_records': len(df),
#             'unique_athletes': df['name'].nunique() if 'name' in df.columns else 0,
#             'unique_countries': df['country'].nunique() if 'country' in df.columns else 0,
#             'year_range': (df['year'].min(), df['year'].max()) if 'year' in df.columns else (0, 0),
#             'disciplines': df['discipline'].value_counts().to_dict() if 'discipline' in df.columns else {},
#             'genders': df['gender'].value_counts().to_dict() if 'gender' in df.columns else {},
#         }
#         return overview
#     except Exception as e:
#         st.error(f"Error getting data overview: {e}")
#         return {}

# def run_data_pipeline():
#     """Run the complete data pipeline if needed."""
#     if st.button("🔄 Run Full Data Pipeline"):
#         with st.spinner("Running data pipeline... This may take several minutes."):
#             try:
#                 # Initialize manager and run
#                 manager = IFSCDataManager()
                
#                 # Check if we need initial fetch
#                 leagues_file = Path("IFSC_Data/all_years_leagues.csv")
#                 if not leagues_file.exists():
#                     st.info("No existing data found. Running initial fetch...")
#                     manager.initial_data_fetch(test_mode=True)  # Use test mode for faster demo
#                 else:
#                     st.info("Running incremental update...")
#                     manager.update_existing_data()
                
#                 st.success("Data pipeline completed successfully!")
#                 st.rerun()
                
#             except Exception as e:
#                 st.error(f"Pipeline error: {e}")
#                 st.exception(e)

# def main():
#     # Header
#     st.title("🧗‍♂️ Climbing Competition Analysis Dashboard")
    
#     # Check data availability
#     if not check_data_availability():
#         st.subheader("Setup Required")
#         run_data_pipeline()
#         return
    
#     # Load components
#     aggregator, calculator = load_components()
    
#     if None in (aggregator, calculator):
#         st.error("Failed to initialize analysis components.")
#         return
    
#     # Get data overview
#     overview = get_data_overview()
    
#     if not overview or overview.get('total_records', 0) == 0:
#         st.warning("No competition data found.")
#         run_data_pipeline()
#         return
    
#     # Display basic stats in sidebar
#     with st.sidebar:
#         st.subheader("📊 Data Overview")
#         st.metric("Total Records", f"{overview.get('total_records', 0):,}")
#         st.metric("Athletes", f"{overview.get('unique_athletes', 0):,}")
#         st.metric("Countries", f"{overview.get('unique_countries', 0):,}")
        
#         year_range = overview.get('year_range', (0, 0))
#         st.metric("Years", f"{year_range[0]}-{year_range[1]}")
        
#         # Refresh button
#         if st.button("🔄 Refresh Data"):
#             st.cache_resource.clear()
#             st.rerun()
    
#     # Create filters object
#     filters = {
#         'year_range': overview.get('year_range'),
#         'disciplines': list(overview.get('disciplines', {}).keys()),
#         'genders': list(overview.get('genders', {}).keys()),
#         'countries': None,
#     }
    
#     # Main content - Start with ELO tab
#     tab1, tab2, tab3 = st.tabs([
#         "🎯 ELO Rankings", 
#         "📈 Overview", 
#         "🏆 Athletes"
#     ])
    
#     with tab1:
#         try:
#             streamlit_elo.render(None, calculator, filters)  # analyzer not needed
#         except Exception as e:
#             st.error(f"Error in ELO tab: {e}")
#             st.exception(e)
    
#     with tab2:
#         st.subheader("📈 Data Overview")
        
#         # Basic statistics
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             st.metric("Total Records", f"{overview.get('total_records', 0):,}")
#             st.metric("Unique Athletes", f"{overview.get('unique_athletes', 0):,}")
        
#         with col2:
#             disciplines = overview.get('disciplines', {})
#             st.write("**Disciplines:**")
#             for disc, count in disciplines.items():
#                 st.write(f"- {disc}: {count:,}")
        
#         with col3:
#             genders = overview.get('genders', {})
#             st.write("**Gender Distribution:**")
#             for gender, count in genders.items():
#                 st.write(f"- {gender}: {count:,}")
    
#     with tab3:
#         st.subheader("🏆 Athletes")
#         st.info("Athlete analysis features coming soon...")

# if __name__ == "__main__":
#     main()

# import streamlit as st
# import pandas as pd
# import sys
# import os
# from pathlib import Path
# import warnings

# # Import utility modules
# try:
#     from utils.scraper_init import IFSCScraper
#     from utils.main import IFSCDataManager
#     from utils.data_aggregator import IFSCDataAggregator
#     from utils.elo_scoring import ELOCalculator
#     from utils import streamlit_elo
#     from utils import streamlit_overview
# except ImportError as e:
#     st.error(f"Import error: {e}")
#     st.error("Please ensure all utility modules are in the 'utils/' directory")
#     st.stop()

# warnings.filterwarnings('ignore')

# # Page configuration
# st.set_page_config(
#     page_title="Climbing Competition Analysis",
#     page_icon="🧗‍♂️",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# @st.cache_resource
# def load_components():
#     """Initialize analysis components."""
#     try:
#         aggregator = IFSCDataAggregator()
#         calculator = ELOCalculator()
#         return aggregator, calculator
#     except Exception as e:
#         st.error(f"Error initializing components: {e}")
#         return None, None

# def check_data_availability():
#     """Check if required data files exist."""
#     required_paths = [
#         Path("Data/aggregate_data"),
#     ]
    
#     missing_paths = [p for p in required_paths if not p.exists()]
    
#     if missing_paths:
#         st.error("Missing required data directories:")
#         for path in missing_paths:
#             st.write(f"- {path}")
        
#         st.markdown("""
#         **To fix this:**
#         1. Run the data pipeline using main.py first
#         2. Ensure your folder structure has:
#         ```
#         Data/
#         └── aggregate_data/
#             ├── aggregated_results.csv
#             └── [era files].csv
#         ```
#         """)
#         return False
    
#     return True

# def run_data_pipeline():
#     """Run the complete data pipeline if needed."""
#     if st.button("🔄 Run Full Data Pipeline"):
#         with st.spinner("Running data pipeline... This may take several minutes."):
#             try:
#                 # Initialize manager and run
#                 manager = IFSCDataManager()
                
#                 # Check if we need initial fetch
#                 leagues_file = Path("IFSC_Data/all_years_leagues.csv")
#                 if not leagues_file.exists():
#                     st.info("No existing data found. Running initial fetch...")
#                     manager.initial_data_fetch(test_mode=True)  # Use test mode for faster demo
#                 else:
#                     st.info("Running incremental update...")
#                     manager.update_existing_data()
                
#                 st.success("Data pipeline completed successfully!")
#                 st.rerun()
                
#             except Exception as e:
#                 st.error(f"Pipeline error: {e}")
#                 st.exception(e)

# def main():
#     # Header
#     st.title("🧗‍♂️ Climbing Competition Analysis Dashboard")
    
#     # Check data availability
#     if not check_data_availability():
#         st.subheader("Setup Required")
#         run_data_pipeline()
#         return
    
#     # Load components
#     aggregator, calculator = load_components()
    
#     if None in (aggregator, calculator):
#         st.error("Failed to initialize analysis components.")
#         return
    
#     # Create tabs for different analyses
#     tab1, tab2, tab3, tab4, tab5 = st.tabs([
#         "🎯 ELO Rankings", 
#         "📊 Overview", 
#         "🌍 Countries",
#         "🏆 Athletes", 
#         "📈 Deep Analytics"
#     ])
    
#     with tab1:
#         try:
#             streamlit_elo.render(None, calculator, None)
#         except Exception as e:
#             st.error(f"Error in ELO tab: {e}")
#             st.exception(e)
    
#     with tab2:
#         try:
#             streamlit_overview.render()
#         except Exception as e:
#             st.error(f"Error in Overview tab: {e}")
#             st.exception(e)
    
#     with tab3:
#         st.subheader("🌍 Country Performance Analysis")
        
#         # Country analysis placeholder
#         st.info("Country deep-dive analysis coming soon...")
        
#         st.markdown("""
#         **Planned Features:**
#         - Country performance trends by discipline and year
#         - Medal counts and podium finishes by nation
#         - Participation growth by country
#         - Regional strength analysis
#         - Head-to-head country comparisons
#         """)
    
#     with tab4:
#         st.subheader("🏆 Individual Athlete Analysis")
        
#         # Athlete analysis placeholder  
#         st.info("Individual athlete analysis coming soon...")
        
#         st.markdown("""
#         **Planned Features:**
#         - Career progression tracking
#         - Peak performance identification
#         - Head-to-head athlete comparisons
#         - Competition consistency analysis
#         - Injury/break pattern detection
#         """)
    
#     with tab5:
#         st.subheader("📈 Advanced Analytics")
        
#         # Advanced analytics placeholder
#         st.info("Advanced analytics coming soon...")
        
#         st.markdown("""
#         **Planned Features:**
#         - **Yearly Trends**: Track how climbing performance and participation evolved over time
#         - **Career Progression**: Analyze individual athlete development and peak performance periods  
#         - **Head-to-Head Comparison**: Compare two athletes across multiple metrics and competitions
#         - **Location Performance**: See how different venues and countries affect performance
#         - **Discipline Crossover**: Analyze athletes who compete across multiple climbing disciplines
#         - **Seasonal Patterns**: Identify performance patterns throughout the competition calendar
#         - **Scoring System Impact**: Analyze how rule changes affected competition outcomes
#         """)

# if __name__ == "__main__":
#     main()

import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
import warnings

# Import utility modules
try:
    from utils.scraper_init import IFSCScraper
    from utils.main import IFSCDataManager
    from utils.data_aggregator import IFSCDataAggregator
    from utils.elo_scoring import ELOCalculator
    from utils import streamlit_elo
    from utils import streamlit_overview
    from utils import streamlit_countries
    from utils import streamlit_athlete
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please ensure all utility modules are in the 'utils/' directory")
    st.stop()

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Climbing Competition Analysis",
    page_icon="🧗‍♂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def load_components():
    """Initialize analysis components."""
    try:
        aggregator = IFSCDataAggregator()
        calculator = ELOCalculator()
        return aggregator, calculator
    except Exception as e:
        st.error(f"Error initializing components: {e}")
        return None, None

def check_data_availability():
    """Check if required data files exist."""
    required_paths = [
        Path("Data/aggregate_data"),
    ]
    
    missing_paths = [p for p in required_paths if not p.exists()]
    
    if missing_paths:
        st.error("Missing required data directories:")
        for path in missing_paths:
            st.write(f"- {path}")
        
        st.markdown("""
        **To fix this:**
        1. Run the data pipeline using main.py first
        2. Ensure your folder structure has:
        ```
        Data/
        └── aggregate_data/
            ├── aggregated_results.csv
            └── [era files].csv
        ```
        """)
        return False
    
    return True

def run_data_pipeline():
    """Run the complete data pipeline if needed."""
    if st.button("🔄 Run Full Data Pipeline"):
        with st.spinner("Running data pipeline... This may take several minutes."):
            try:
                # Initialize manager and run
                manager = IFSCDataManager()
                
                # Check if we need initial fetch
                leagues_file = Path("IFSC_Data/all_years_leagues.csv")
                if not leagues_file.exists():
                    st.info("No existing data found. Running initial fetch...")
                    manager.initial_data_fetch(test_mode=True)  # Use test mode for faster demo
                else:
                    st.info("Running incremental update...")
                    manager.update_existing_data()
                
                st.success("Data pipeline completed successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                st.exception(e)

def main():
    # Header
    st.title("🧗‍♂️ Climbing Competition Analysis Dashboard")
    
    # Check data availability
    if not check_data_availability():
        st.subheader("Setup Required")
        run_data_pipeline()
        return
    
    # Load components
    aggregator, calculator = load_components()
    
    if None in (aggregator, calculator):
        st.error("Failed to initialize analysis components.")
        return
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs([
        "ELO Rankings", 
        "Overview", 
        "Countries",
        "Athletes & Analytics"
    ])
    
    with tab1:
        try:
            streamlit_elo.render(None, calculator, None)
        except Exception as e:
            st.error(f"Error in ELO tab: {e}")
            st.exception(e)
    
    with tab2:
        try:
            streamlit_overview.render()
        except Exception as e:
            st.error(f"Error in Overview tab: {e}")
            st.exception(e)
    
    with tab3:
        try:
            streamlit_countries.render()
        except Exception as e:
            st.error(f"Error in Countries tab: {e}")
            st.exception(e)
    
    with tab4:
        try:
            streamlit_athlete.render()
        except Exception as e:
            st.error(f"Error in Athletes tab: {e}")
            st.exception(e)

if __name__ == "__main__":
    main()