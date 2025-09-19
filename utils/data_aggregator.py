import pandas as pd
import numpy as np
from pathlib import Path
import re
from datetime import datetime
import warnings
import logging

warnings.filterwarnings('ignore')

class IFSCDataAggregator:
    """Streamlined IFSC climbing competition data aggregator with robust error handling."""
    
    def __init__(self, data_dir: str = "./IFSC_Data/API_Results_Expanded", output_dir: str = "./Data"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.results_df = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Define scoring system eras
        self.scoring_systems = {
            'Lead': {
                'IFSC_Modern_2007-2025': {'start': 2007, 'end': 2025},
                'UIAA_Legacy_1991-2006': {'start': 1991, 'end': 2006}
            },
            'Boulder': {
                'IFSC_AddedPoints_2025-2025': {'start': 2025, 'end': 2025},
                'IFSC_ZoneTop_2007-2024': {'start': 2007, 'end': 2024},
                'UIAA_Legacy_1991-2006': {'start': 1991, 'end': 2006}
            },
            'Speed': {
                'IFSC_Time_2009-2025': {'start': 2009, 'end': 2025},
                'IFSC_Score_2007-2008': {'start': 2007, 'end': 2008},
                'UIAA_Legacy_1991-2006': {'start': 1991, 'end': 2006}
            }
        }
        
        # Create output directories
        (self.output_dir / "aggregate_data").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "data_summary").mkdir(parents=True, exist_ok=True)
    
    def aggregate_all_results(self) -> pd.DataFrame:
        """Load and combine all result CSV files with robust error handling."""
        self.logger.info("Loading all result files...")
        
        all_results = []
        csv_files = list(self.data_dir.rglob("*.csv"))
        
        failed_files = []
        
        for csv_file in csv_files:
            try:
                # Read with error handling for encoding issues
                df = pd.read_csv(csv_file, encoding='utf-8', on_bad_lines='skip')
                
                if not df.empty and 'name' in df.columns:
                    df['_file'] = csv_file.name
                    df['file_path'] = str(csv_file.relative_to(self.data_dir))
                    all_results.append(df)
                    
            except Exception as e:
                failed_files.append((csv_file.name, str(e)))
                continue
        
        if failed_files:
            self.logger.warnsourceing(f"Failed to load {len(failed_files)} files")
        
        if not all_results:
            raise ValueError("No valid result files could be loaded")
        
        # Combine all results
        self.results_df = pd.concat(all_results, ignore_index=True, sort=False)
        self.logger.info(f"Loaded {len(csv_files)} files, {len(self.results_df)} total records")
        
        # Process the data
        self._clean_data()
        # self._extract_metadata()
        self._classify_scoring_systems()
        # self._save_all_data()
        
        self.results_df.sort_values(by=['start_date'], inplace=True)
        return self.results_df
    
    def _clean_data(self):
        """Clean and standardize data with minimal processing."""
        self.logger.info("Cleaning data...")
        
        # Standardize column names
        self.results_df.columns = [col.lower().strip().replace(' ', '_') for col in self.results_df.columns]
        
        # Remove completely empty rows
        self.results_df = self.results_df.dropna(how='all')
        
        # Ensure essential columns exist
        required_cols = ['name', 'source_file']
        missing_cols = [col for col in required_cols if col not in self.results_df.columns]
        
        if missing_cols:
            self.logger.warning(f"Missing required columns: {missing_cols}")
        
        # Clean name column
        if 'name' in self.results_df.columns:
            self.results_df['name'] = self.results_df['name'].astype(str).str.strip()
            self.results_df = self.results_df[~self.results_df['name'].isin(['', 'nan', 'None'])]
        
        self.results_df['processed_at'] = datetime.now()
        
    # def _extract_metadata(self):
    #     """Extract metadata from filenames and add into new columns"""
    #     self.logger.info("Extracting metadata from filenames...")
        
    #     def parse_filename(filename):
    #         """Parse competition metadata from filename."""
            
    #         base_name = filename.replace('.csv', '')
    #         # Expected format: YYYY-MM-DD_Location_Discipline_Gender_Round.csv
    #         parts = base_name.split('_')
            
    #         if len(parts) >= 4:
    #             date_part = parts[0]
    #             location = parts[1] if len(parts) > 1 else 'Unknown'
    #             discipline = parts[2] if len(parts) > 2 else 'Unknown'
    #             gender = parts[3] if len(parts) > 3 else 'Unknown'
    #             round_name = parts[4] if len(parts) > 4 else 'Unknown'
                
    #             # Extract year
    #             year_match = re.search(r'(\d{4})', date_part)
    #             year = int(year_match.group(1)) if year_match else 2000
                
    #             return {
    #                 'comp_date': date_part,
    #                 'location': location,
    #                 'discipline': discipline,
    #                 'gender': gender,
    #                 'round': round_name,
    #                 'year': year
    #             }
    #         else:
    #             # Fallback parsing
    #             year_match = re.search(r'(\d{4})', base_name)
    #             return {
    #                 'comp_date': 'unknown',
    #                 'location': 'Unknown',
    #                 'discipline': 'Unknown',
    #                 'gender': 'Unknown', 
    #                 'round': 'Unknown',
    #                 'year': int(year_match.group(1)) if year_match else 2000
    #             }
                    
           
        
    #     # Apply parsing to each file
    #     metadata_list = []
    #     for _, row in self.results_df.iterrows():
    #         filename = row['source_file']
    #         metadata = parse_filename(filename)
    #         metadata_list.append(metadata)
        
    #     # Add metadata columns
    #     metadata_df = pd.DataFrame(metadata_list)
    #     self.results_df = pd.concat([self.results_df, metadata_df], axis=1)
        
    #     # Create start_date from comp_date
    #     self.results_df['start_date'] = pd.to_datetime(
    #         self.results_df['comp_date'], 
    #         errors='coerce'
    #     )
        
    #     # Fallback to year-based date for invalid dates
    #     invalid_dates = self.results_df['start_date'].isna()
    #     self.results_df.loc[invalid_dates, 'start_date'] = pd.to_datetime(
    #         self.results_df.loc[invalid_dates, 'year'].astype(str) + '-01-01'
    #     )
        
    def _classify_scoring_systems(self):
        """Classify records by scoring system era."""
        
        def get_scoring_era(row):
            discipline = row['discipline']
            year = row['year']
            
            # Normalize discipline names
            discipline_map = {
                'L': 'Lead',    'Lead': 'Lead', 
                'B': 'Boulder', 'Boulder': 'Boulder',
                'S': 'Speed',   'Speed': 'Speed'
            }
            discipline = discipline_map.get(discipline, discipline)
            
            if discipline not in self.scoring_systems:
                return f'{discipline}_Unknown'
            
            # Find matching era
            for era_name, era_info in self.scoring_systems[discipline].items():
                if era_info['start'] <= year <= era_info['end']:
                    return f'{discipline}_{era_name}'
            
            return f'{discipline}_Unknown'
        
        self.results_df['scoring_era'] = self.results_df.apply(get_scoring_era, axis=1)
        
       
    # def _save_all_data(self):
    #     """Save processed data with proper organization."""
    #     self.logger.info("Saving processed data...")
        
    #     # Save main aggregated file
    #     main_file = self.output_dir / "aggregate_data" / "aggregated_results.csv"
    #     self.results_df.to_csv(main_file, index=False)
    #     self.logger.info(f"Saved main file: {main_file} ({len(self.results_df)} records)")
        
    #     self._save_era_files()
    
    # def _save_era_files(self):
    #     """Save era-specific files for analysis."""
    #     self.logger.info("Saving era-based files...")
        
    #     raw_data_dir = self.output_dir / "aggregate_data"
        
    #     # Skip unknown eras
    #     valid_df = self.results_df[~self.results_df['scoring_era'].str.contains('Unknown')]
        
    #     if valid_df.empty:
    #         self.logger.warning("No valid scoring era data to save")
    #         return
        
    #     for (era, gender), group_df in valid_df.groupby(['scoring_era', 'gender']):
    #         if len(group_df) < 10:  # Skip very small datasets
    #             continue
                
    #         filename = f"{era}_{gender}.csv"
    #         filepath = raw_data_dir / filename
            
    #         group_df.to_csv(filepath, index=False)
            
            
    
    def load_existing_results(self) -> pd.DataFrame:
        """Load existing aggregated results."""
        results_file = self.output_dir / "aggregate_data" / "aggregated_results.csv"
        
        if not results_file.exists():
            raise FileNotFoundError(f"Aggregated results not found: {results_file}")
        
        self.results_df = pd.read_csv(results_file)
        self.logger.info(f"Loaded existing results: {len(self.results_df)} records")
        return self.results_df
    
    def update_results(self, df_list: list) -> pd.DataFrame: 
        """Update existing results with new data."""
        old_result_file = self.output_dir / "aggregate_data" / "aggregated_results.csv"
        
        if old_result_file.exists():
            old_result_df = pd.read_csv(old_result_file)
        else:
            old_result_df = pd.DataFrame()
        
        # Concatenate new dataframes
        if df_list:
            new_result_df = pd.concat(df_list, ignore_index=True, sort=False)
            self.logger.info(f"Processing {len(df_list)} new files, {len(new_result_df)} new records")
            
            # Set the new data as current results_df for processing
            self.results_df = new_result_df
            
            # Process the new data
            self._clean_data()
            self._classify_scoring_systems()
            
            # Combine old and new data
            if not old_result_df.empty:
                combined_df = pd.concat([old_result_df, self.results_df], ignore_index=True, sort=False)
            else:
                combined_df = self.results_df.copy()
            
            # Remove duplicates based on key columns if they exist
            if all(col in combined_df.columns for col in ['name', 'year', 'discipline', 'gender']):
                combined_df = combined_df.drop_duplicates(subset=['name', 'year', 'discipline', 'gender'], keep='last')
            
            self.results_df = combined_df
            return combined_df
        else:
            self.logger.info("No new data to process")
            return old_result_df