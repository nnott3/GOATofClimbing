import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
import warnings

warnings.filterwarnings('ignore')

class ClimbingAnalyzer:
    """Optimized climbing competition data analyzer with robust error handling."""
    
    def __init__(self, data_dir: str = "./Data"):
        self.data_dir = Path(data_dir)
        self.aggregated_df = None
        self.era_files = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Color scheme for consistency
        self.discipline_colors = {
            'Boulder': '#e74c3c',
            'Lead': '#3498db', 
            'Speed': '#2ecc71',
            'Combined': '#f39c12'
        }
        
        self._load_data()
    
    def _load_data(self):
        """Load all available data files with error handling."""
        if not self.data_dir.exists():
            self.logger.error(f"Data directory not found: {self.data_dir}")
            return
        
        self.logger.info(f"Loading data from: {self.data_dir}")
        
        # Load main aggregated file
        agg_file = self.data_dir / "aggregate_data" / "aggregated_results.csv"
        if agg_file.exists():
            try:
                self.aggregated_df = pd.read_csv(agg_file)
                self._clean_aggregated_data()
                self.logger.info(f"Loaded aggregated data: {len(self.aggregated_df)} records")
            except Exception as e:
                self.logger.error(f"Error loading aggregated data: {e}")
        
        # Load era-specific files
        era_dir = self.data_dir / "aggregate_data"
        if era_dir.exists():
            for csv_file in era_dir.glob("*.csv"):
                if csv_file.name != "aggregated_results.csv":
                    try:
                        era_data = pd.read_csv(csv_file)
                        if not era_data.empty:
                            self.era_files[csv_file.stem] = era_data
                            self.logger.info(f"Loaded era file: {csv_file.stem}")
                    except Exception as e:
                        self.logger.warning(f"Error loading {csv_file}: {e}")
    
    def _clean_aggregated_data(self):
        """Clean and optimize the main dataset."""
        if self.aggregated_df is None:
            return
        
        # Convert date columns efficiently
        date_columns = ['start_date', 'comp_date']
        for col in date_columns:
            if col in self.aggregated_df.columns:
                self.aggregated_df[col] = pd.to_datetime(
                    self.aggregated_df[col], errors='coerce'
                )
        
        # Optimize numeric columns
        numeric_columns = ['year', 'round_rank']
        for col in numeric_columns:
            if col in self.aggregated_df.columns:
                self.aggregated_df[col] = pd.to_numeric(
                    self.aggregated_df[col], errors='coerce'
                )
        
        # Clean text columns
        text_columns = ['name', 'country', 'discipline', 'gender']
        for col in text_columns:
            if col in self.aggregated_df.columns:
                self.aggregated_df[col] = (
                    self.aggregated_df[col]
                    .astype(str)
                    .str.strip()
                    .str.replace('nan', '')
                )
        
        # Remove invalid records
        if 'name' in self.aggregated_df.columns:
            self.aggregated_df = self.aggregated_df[
                (self.aggregated_df['name'] != '') & 
                (self.aggregated_df['name'] != 'nan')
            ]
        
        # Standardize country codes
        if 'country' in self.aggregated_df.columns:
            self.aggregated_df['country'] = self.aggregated_df['country'].str.upper()
    
    def get_data_overview(self) -> Dict:
        """Generate comprehensive data overview with error handling."""
        if self.aggregated_df is None or self.aggregated_df.empty:
            return {
                'total_records': 0,
                'unique_athletes': 0,
                'unique_countries': 0,
                'year_range': (0, 0),
                'disciplines': {},
                'genders': {},
                'error': 'No data loaded'
            }
        
        try:
            # Filter to valid disciplines only
            valid_disciplines = ['Boulder', 'Lead', 'Speed', 'B', 'L', 'S']
            
            # Use discipline column if available, otherwise use comp_discipline
            discipline_col = 'discipline' if 'discipline' in self.aggregated_df.columns else 'comp_discipline'
            
            if discipline_col in self.aggregated_df.columns:
                filtered_df = self.aggregated_df[
                    self.aggregated_df[discipline_col].isin(valid_disciplines)
                ]
            else:
                filtered_df = self.aggregated_df
            
            # Use gender column if available, otherwise use comp_gender
            gender_col = 'gender' if 'gender' in self.aggregated_df.columns else 'comp_gender'
            
            overview = {
                'total_records': len(filtered_df),
                'unique_athletes': filtered_df['name'].nunique() if 'name' in filtered_df.columns else 0,
                'unique_countries': filtered_df['country'].nunique() if 'country' in filtered_df.columns else 0,
                'year_range': (
                    int(filtered_df['year'].min()) if 'year' in filtered_df.columns else 0,
                    int(filtered_df['year'].max()) if 'year' in filtered_df.columns else 0
                ),
                'disciplines': (
                    filtered_df[discipline_col].value_counts().to_dict() 
                    if discipline_col in filtered_df.columns else {}
                ),
                'genders': (
                    filtered_df[gender_col].value_counts().to_dict() 
                    if gender_col in filtered_df.columns else {}
                ),
                'era_files': list(self.era_files.keys())
            }
            
            return overview
            
        except Exception as e:
            self.logger.error(f"Error generating overview: {e}")
            return {
                'total_records': 0,
                'unique_athletes': 0,
                'unique_countries': 0,
                'year_range': (0, 0),
                'disciplines': {},
                'genders': {},
                'error': str(e)
            }
    
    def filter_data(self, df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """Apply filters to dataframe with robust error handling."""
        if df is None or df.empty:
            return pd.DataFrame()
        
        filtered_df = df.copy()
        
        try:
            # Year range filter
            if filters.get('year_range') and 'year' in filtered_df.columns:
                start_year, end_year = filters['year_range']
                filtered_df = filtered_df[
                    (filtered_df['year'] >= start_year) & 
                    (filtered_df['year'] <= end_year)
                ]
            
            # Discipline filter
            if filters.get('disciplines'):
                discipline_col = 'discipline' if 'discipline' in filtered_df.columns else 'comp_discipline'
                if discipline_col in filtered_df.columns:
                    filtered_df = filtered_df[
                        filtered_df[discipline_col].isin(filters['disciplines'])
                    ]
            
            # Gender filter
            if filters.get('genders'):
                gender_col = 'gender' if 'gender' in filtered_df.columns else 'comp_gender'
                if gender_col in filtered_df.columns:
                    filtered_df = filtered_df[
                        filtered_df[gender_col].isin(filters['genders'])
                    ]
            
            # Country filter
            if filters.get('countries') and 'country' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['country'].isin(filters['countries'])
                ]
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
            return df  # Return original data if filtering fails
        
        return filtered_df
    
    def get_athlete_stats(self, filters: Dict = None) -> pd.DataFrame:
        """Generate athlete statistics with comprehensive error handling."""
        if self.aggregated_df is None or self.aggregated_df.empty:
            return pd.DataFrame()
        
        try:
            df = self.aggregated_df.copy()
            if filters:
                df = self.filter_data(df, filters)
            
            if df.empty or 'name' not in df.columns:
                return pd.DataFrame()
            
            # Ensure we have required columns
            required_cols = ['name', 'round_rank']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                self.logger.error(f"Missing required columns for athlete stats: {missing_cols}")
                return pd.DataFrame()
            
            # Calculate statistics
            athlete_stats = df.groupby(['name']).agg({
                'round_rank': [
                    'count',
                    'mean', 
                    lambda x: (x == 1).sum(),  # wins
                    lambda x: (x <= 3).sum()   # podiums
                ],
                'year': ['min', 'max'] if 'year' in df.columns else ['count', 'count']
            }).round(2)
            
            # Flatten column names
            athlete_stats.columns = ['_'.join([str(c) for c in col]) for col in athlete_stats.columns]
            athlete_stats = athlete_stats.reset_index()
            
            # Rename columns for clarity
            column_mapping = {
                'round_rank_count': 'total_competitions',
                'round_rank_mean': 'avg_rank',
                'round_rank_<lambda_0>': 'wins',
                'round_rank_<lambda_1>': 'podiums'
            }
            
            if 'year' in df.columns:
                column_mapping.update({
                    'year_min': 'career_start',
                    'year_max': 'career_end'
                })
            
            athlete_stats.rename(columns=column_mapping, inplace=True)
            
            # Calculate rates
            if 'total_competitions' in athlete_stats.columns:
                athlete_stats['win_rate'] = (
                    athlete_stats.get('wins', 0) / athlete_stats['total_competitions'] * 100
                ).round(2)
                athlete_stats['podium_rate'] = (
                    athlete_stats.get('podiums', 0) / athlete_stats['total_competitions'] * 100
                ).round(2)
            
            return athlete_stats.sort_values('total_competitions', ascending=False)
            
        except Exception as e:
            self.logger.error(f"Error calculating athlete stats: {e}")
            return pd.DataFrame()
    
    def get_country_stats(self, filters: Dict = None) -> pd.DataFrame:
        """Generate country statistics with error handling."""
        if self.aggregated_df is None or self.aggregated_df.empty:
            return pd.DataFrame()
        
        try:
            df = self.aggregated_df.copy()
            if filters:
                df = self.filter_data(df, filters)
            
            if df.empty or 'country' not in df.columns:
                return pd.DataFrame()
            
            # Calculate country statistics
            country_stats = df.groupby('country').agg({
                'name': 'nunique',
                'round_rank': [
                    'count',
                    lambda x: (x == 1).sum(),  # wins
                    lambda x: (x <= 3).sum()   # podiums
                ] if 'round_rank' in df.columns else ['count', 'count', 'count']
            })
            
            # Flatten column names
            country_stats.columns = ['_'.join([str(c) for c in col]) for col in country_stats.columns]
            country_stats = country_stats.reset_index()
            
            # Rename columns
            country_stats.rename(columns={
                'name_nunique': 'total_athletes',
                'round_rank_count': 'total_participations',
                'round_rank_<lambda_0>': 'total_wins',
                'round_rank_<lambda_1>': 'total_podiums'
            }, inplace=True)
            
            return country_stats.sort_values('total_athletes', ascending=False)
            
        except Exception as e:
            self.logger.error(f"Error calculating country stats: {e}")
            return pd.DataFrame()
    
    def is_data_available(self) -> bool:
        """Check if data is available for analysis."""
        return (
            self.aggregated_df is not None and 
            not self.aggregated_df.empty and
            len(self.aggregated_df) > 0
        )