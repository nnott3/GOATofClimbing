import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
    st.error(f"Import error eieieie: {e}")
    st.error("Please ensure all utility modules are in the 'utils/' directory")
    st.stop()

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Climbing Competition Analysis",
    page_icon="🧗‍♂️",
    layout="wide",
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
        "📈 ELO Rankings", 
        "🎯 Overview", 
        "🌍 Countries",
        "🔍 Athlete Deep Dive"
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