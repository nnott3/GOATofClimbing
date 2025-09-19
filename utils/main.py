# import pandas as pd
# import time
# from pathlib import Path
# from datetime import datetime
# from utils.scraper_init import IFSCScraper
# import sys

# class IFSCIncrementalFetcher:
#     def __init__(self):
#         self.scraper = IFSCScraper()
#         self.data_dir = Path('IFSC_Data')
#         self.leagues_file = self.data_dir / 'all_years_leagues.csv'
#         self.metadata_dir = self.data_dir / 'API_Event_metadata'
    
#     def get_existing_data(self, file_path):
#         """Load existing CSV or return empty DataFrame."""
#         return pd.read_csv(file_path) if file_path.exists() else pd.DataFrame()
    
#     def find_new_leagues(self, current_leagues, existing_leagues):
#         """Find leagues that don't exist in database."""
#         if existing_leagues.empty:
#             return current_leagues
        
#         existing_keys = set(zip(existing_leagues['year'], existing_leagues['league_name']))
#         current_keys = set(zip(current_leagues['year'], current_leagues['league_name']))
#         new_keys = current_keys - existing_keys
        
#         if new_keys:
#             return current_leagues[
#                 current_leagues.apply(lambda x: (x['year'], x['league_name']) in new_keys, axis=1)
#             ]
#         return pd.DataFrame()
    
#     def find_new_events(self, current_events, existing_events):
#         """Find events that don't exist in database."""
#         if existing_events.empty:
#             return current_events
        
#         existing_keys = set()
#         for _, row in existing_events.iterrows():
#             key = (row['event_id'], row['discipline'], row['gender'], row.get('round', 'N/A'))
#             existing_keys.add(key)
        
#         new_events = []
#         for _, row in current_events.iterrows():
#             key = (row['event_id'], row['discipline'], row['gender'], row.get('round', 'N/A'))
#             if key not in existing_keys:
#                 new_events.append(row)
        
#         return pd.DataFrame(new_events) if new_events else pd.DataFrame()
    
#     def should_update_year(self, year):
#         """Check if year should be updated (current and next year only)."""
#         current_year = datetime.now().year
#         return year >= current_year
    
#     def fetch_results_for_events(self, events_df):
#         """Fetch results for given events."""
#         for _, event in events_df.iterrows():
#             try:
#                 self.scraper.parse_round_result(event.to_dict())
#             except Exception as e:
#                 print(f"Error processing {event.get('event_name', 'Unknown')}: {e}")
    
#     def run_update(self):
#         """Run incremental update - check for new leagues and events."""
#         print("Starting incremental update...")
#         start_time = time.time()
        
#         # Update leagues
#         current_leagues = self.scraper.get_worldcup_leagues()
#         existing_leagues = self.get_existing_data(self.leagues_file)
#         new_leagues = self.find_new_leagues(current_leagues, existing_leagues)
        
#         print(f"Found {len(new_leagues)} new leagues")
        
#         # Check existing leagues for new events
#         all_new_events = pd.DataFrame()
        
#         for _, league in existing_leagues.iterrows():
#             year = league['year']
#             if not self.should_update_year(year):
#                 continue
                
#             events_file = self.metadata_dir / f"{year}_event_meta.csv"
#             existing_events = self.get_existing_data(events_file)
#             current_events = self.scraper.get_events_from_league(league['url'])
            
#             new_events = self.find_new_events(current_events, existing_events)
#             if not new_events.empty:
#                 all_new_events = pd.concat([all_new_events, new_events], ignore_index=True)
        
#         # Process completely new leagues
#         for _, league in new_leagues.iterrows():
#             new_events = self.scraper.get_events_from_league(league['url'])
#             if not new_events.empty:
#                 all_new_events = pd.concat([all_new_events, new_events], ignore_index=True)
        
#         # Fetch results for new events
#         if not all_new_events.empty:
#             print(f"Fetching results for {len(all_new_events)} new events...")
#             self.fetch_results_for_events(all_new_events)
#         else:
#             print("No new events found")
        
#         print(f"Update completed in {(time.time() - start_time)/60:.1f} minutes")
    
#     def run_initial_fetch(self, start_year=None, end_year=None):
#         """Run complete initial fetch."""
#         print("Starting initial fetch...")
#         start_time = time.time()
        
#         leagues_df = self.get_existing_data(self.leagues_file)
#         if leagues_df.empty:
#             leagues_df = self.scraper.get_worldcup_leagues()
        
#         # Filter by year range
#         if start_year:
#             leagues_df = leagues_df[leagues_df['year'] >= start_year]
#         if end_year:
#             leagues_df = leagues_df[leagues_df['year'] <= end_year]
        
#         for _, league in leagues_df.iterrows():
#             year = league['year']
#             print(f"Processing {year}...")
            
#             try:
#                 events_df = self.scraper.get_events_from_league(league['url'])
#                 if not events_df.empty:
#                     self.fetch_results_for_events(events_df)
#             except Exception as e:
#                 print(f"Error processing {year}: {e}")
        
#         print(f"Scraping took a while, it was {(time.time() - start_time)/60:.1f} minutes")


# # Usage
# if __name__ == "__main__":
    
#     fetcher = IFSCIncrementalFetcher()
    
#     if len(sys.argv) > 1 and sys.argv[1] == 'initial':
#         start_year = int(sys.argv[2]) if len(sys.argv) > 2 else None
#         end_year = int(sys.argv[3]) if len(sys.argv) > 3 else None
#         fetcher.run_initial_fetch(start_year, end_year)
#     else:
#         fetcher.run_update()


import pandas as pd
import time
from pathlib import Path
from datetime import datetime
from scraper_init import IFSCScraper
from data_aggregator import IFSCDataAggregator
from elo_scoring import ELOCalculator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IFSCDataManager:
    """Main orchestrator for IFSC data scraping and aggregation."""
    
    def __init__(self):
        self.scraper = IFSCScraper()
        self.aggregator = IFSCDataAggregator()
        self.elo_calculator = ELOCalculator()
        self.data_dir = Path('IFSC_Data')
        self.leagues_file = self.data_dir / 'all_years_leagues.csv'
        self.metadata_dir = self.data_dir / 'API_Event_metadata'
        self.results_dir = self.data_dir / 'API_Results_Expanded'
        
        # Ensure directories exist
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        Path('Data/aggregate_data').mkdir(parents=True, exist_ok=True)
        Path('Elo_Data').mkdir(parents=True, exist_ok=True)
    
    def process_events_for_year(self, year: int, league_url: str) -> list:
        """Process all events for a given year and return list of result DataFrames."""
        logger.info(f"Processing events for {year}...")
        
        # Get events metadata
        events_df = self.scraper.get_events_from_league(league_url)
        if events_df.empty:
            logger.warning(f"No events found for {year}")
            return []
        
        # Save events metadata
        events_df.to_csv(self.metadata_dir / f"{year}_event_meta.csv", index=False)
        
        # Process each event's results
        year_dir = self.results_dir / str(year)
        year_dir.mkdir(exist_ok=True)
        
        result_dfs = []
        for _, event in events_df.iterrows():
            try:
                df, filename = self.scraper.parse_round_result(event.to_dict())
                if not df.empty:
                    # Add source_file column that aggregator expects
                    df['source_file'] = filename
                    df.to_csv(year_dir / filename, index=False)
                    result_dfs.append(df)
            except Exception as e:
                logger.error(f"Failed to process event {event.get('event_name', 'Unknown')}: {e}")
                continue
        
        logger.info(f"Processed {len(result_dfs)} events for {year}")
        return result_dfs
    
    def initial_data_fetch(self, test_mode: bool = False):
        """Perform initial data scraping and aggregation."""
        logger.info("Starting initial data fetch...")
        start_time = time.time()
        
        # Get all leagues
        leagues_df = self.scraper.get_worldcup_leagues()
        leagues_df.to_csv(self.leagues_file, index=False)
        
        # Process leagues (limit to 1 for testing)
        leagues_to_process = leagues_df.head(1) if test_mode else leagues_df
        
        for _, league in leagues_to_process.iterrows():
            self.process_events_for_year(league['year'], league['url'])
        
        # Aggregate all results
        logger.info("Aggregating all results...")
        results_df = self.aggregator.aggregate_all_results()
        results_df.to_csv("Data/aggregate_data/aggregated_results.csv", index=False)
        
        # Save era-specific files
        self._save_era_files(results_df)
        
        # Calculate initial ELO ratings
        logger.info("Calculating initial ELO ratings...")
        self.elo_calculator.calculate_elo_ratings()
        self.elo_calculator.save_results()
        
        elapsed = (time.time() - start_time) / 60
        logger.info(f"Initial fetch completed in {elapsed:.1f} minutes")
    
    def update_existing_data(self):
        """Update existing data with new events."""
        logger.info("Checking for data updates...")
        
        # Load existing leagues
        if not self.leagues_file.exists():
            logger.error("No existing leagues file found. Run initial fetch first.")
            return
        
        df_old_leagues = pd.read_csv(self.leagues_file)
        df_new_leagues = self.scraper.get_worldcup_leagues()
        
        old_years = set(df_old_leagues['year'].tolist())
        new_years = set(df_new_leagues['year'].tolist())
        
        if new_years == old_years:
            # Check latest year for new events
            latest_year = max(old_years)
            logger.info(f"Updating events for latest year: {latest_year}")
            
            league_row = df_new_leagues[df_new_leagues['year'] == latest_year].iloc[0]
            new_result_dfs = self.process_events_for_year(latest_year, league_row['url'])
            
        else:
            # Process new years
            years_to_process = new_years - old_years
            logger.info(f"Processing new years: {sorted(years_to_process)}")
            
            new_result_dfs = []
            for year in sorted(years_to_process):
                league_row = df_new_leagues[df_new_leagues['year'] == year].iloc[0]
                year_results = self.process_events_for_year(year, league_row['url'])
                new_result_dfs.extend(year_results)
            
            # Update leagues file
            df_new_leagues.to_csv(self.leagues_file, index=False)
        
        # Update aggregated results if we have new data
        if new_result_dfs:
            logger.info("Updating aggregated results...")
            updated_results = self.aggregator.update_results(new_result_dfs)
            updated_results.to_csv("Data/aggregate_data/aggregated_results.csv", index=False)
            self._save_era_files(updated_results)
            
            # Update ELO ratings with new data
            logger.info("Updating ELO ratings...")
            new_data_combined = pd.concat(new_result_dfs, ignore_index=True)
            self.elo_calculator.update_elo_ratings(new_data_combined)
        else:
            logger.info("No new data to update")
    
    def _save_era_files(self, results_df: pd.DataFrame):
        """Save era and gender specific files."""
        raw_data_dir = Path("Data/aggregate_data")
        
        # Filter out unknown eras
        valid_df = results_df[~results_df['scoring_era'].str.contains('Unknown', na=False)]
        
        if valid_df.empty:
            logger.warning("No valid scoring era data to save")
            return
        
        for (era, gender), group_df in valid_df.groupby(['scoring_era', 'gender']):
            if len(group_df) < 10:  # Skip small datasets
                continue
            
            filename = f"{era}_{gender}.csv"
            filepath = raw_data_dir / filename
            group_df.to_csv(filepath, index=False)
            logger.info(f"Saved {len(group_df)} records to {filename}")
    
    def get_elo_summary(self, discipline: str = "Boulder", gender: str = "Men", top_n: int = 10):
        """Display current ELO rankings summary."""
        try:
            rankings = self.elo_calculator.get_current_rankings(
                discipline=discipline, gender=gender, top_n=top_n
            )
            if not rankings.empty:
                logger.info(f"\nTop {top_n} {discipline} {gender} ELO Rankings:")
                for i, row in rankings.head(top_n).iterrows():
                    logger.info(f"{i+1:2d}. {row['name']:<25} {row['current_elo']:>4.0f}")
            else:
                logger.warning(f"No rankings found for {discipline} {gender}")
        except Exception as e:
            logger.error(f"Failed to get ELO summary: {e}")

def main():
    """Main execution function."""
    manager = IFSCDataManager()
    
    # Configuration
    FORCE_INITIAL_FETCH = False  # Set to True to force complete re-scraping
    TEST_MODE = False  # Set to True to limit processing for testing
    
    try:
        if FORCE_INITIAL_FETCH or not manager.leagues_file.exists():
            manager.initial_data_fetch(test_mode=TEST_MODE)
        else:
            manager.update_existing_data()
            
        logger.info("Data processing completed successfully")
        
    except Exception as e:
        logger.error(f"Data processing failed: {e}")
        raise

if __name__ == "__main__":
    main()